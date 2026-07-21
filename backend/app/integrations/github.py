from dataclasses import dataclass
import base64
from io import BytesIO
import json
import logging
from pathlib import Path
import tarfile
from typing import Callable, Final, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

from app.core.config import settings

from app.utils.github_manifests import (
    GitHubManifestValidationError,
    GitHubManifestWarning,
    GitHubNormalizedManifest,
    InvalidNormalizedDependencyError,
    limit_discovered_manifest_paths,
    normalize_fixture_manifests,
)

from app.utils.github_url import GitHubRepositoryURL, is_valid_github_repository_identity
from app.utils.github_code_usage_rules import CONFIG_FILENAMES, is_analyzable_source_path, is_test_path


MAX_LANGUAGES: Final = 20
MAX_FILE_TREE_PATHS: Final = 500
MAX_README_CHARS: Final = 10_000
MAX_SOURCE_FILES: Final = 60
MAX_ANONYMOUS_SOURCE_FILES: Final = 20
MAX_MANIFEST_CONTENT_FILES: Final = 10
SOURCE_REQUEST_RESERVE: Final = 1
MAX_SOURCE_FILE_BYTES: Final = 64 * 1024
MAX_ARCHIVE_BYTES: Final = 25 * 1024 * 1024
GITHUB_SNAPSHOT_SCHEMA_VERSION: Final = 3
logger = logging.getLogger(__name__)


class GitHubProviderError(Exception):
    """Base error for GitHub provider failures."""


class GitHubRepositoryNotFoundError(GitHubProviderError):
    """Raised when a requested repository cannot be found."""


class GitHubRateLimitError(GitHubProviderError):
    """Raised when GitHub rejects a request because the rate limit is exhausted."""


class GitHubAuthenticationError(GitHubProviderError):
    """Raised when GitHub rejects configured credentials."""


class GitHubFixtureError(GitHubProviderError):
    """Raised when a local GitHub fixture does not meet the provider contract."""


class GitHubRepositoryIdentityError(GitHubProviderError):
    """Raised when a provider receives a non-normalized repository identity."""


@dataclass(frozen=True, slots=True)
class GitHubRepositorySnapshot:
    canonical_url: str
    repository_name: str
    owner: str
    description: str | None
    default_branch: str | None
    is_public: bool
    is_archived: bool | None
    languages: tuple[str, ...]
    file_tree: tuple[str, ...]
    readme_text: str | None
    manifest_paths: tuple[str, ...]
    is_demo: bool
    schema_version: int = GITHUB_SNAPSHOT_SCHEMA_VERSION
    normalized_manifests: tuple[GitHubNormalizedManifest, ...] = ()
    manifest_warnings: tuple[GitHubManifestWarning, ...] = ()
    source_files: tuple[tuple[str, str], ...] = ()


class GitHubProvider(Protocol):
    def get_repository_snapshot(
        self, repository: GitHubRepositoryURL
    ) -> GitHubRepositorySnapshot: ...


def get_github_provider() -> "GitHubProvider":
    """Return the snapshot provider configured for this process."""
    if settings.github_provider == "demo":
        return DemoGitHubProvider()
    return LiveGitHubProvider(
        token=settings.github_token or None,
        timeout_seconds=settings.github_api_timeout_seconds,
    )


class LiveGitHubProvider:
    """Fetch a bounded, pipeline-compatible snapshot from GitHub's public API."""

    api_base_url: Final = "https://api.github.com"

    def __init__(
        self,
        *,
        token: str | None = None,
        timeout_seconds: int = 20,
        request_json: Callable[[str], object] | None = None,
        request_bytes: Callable[[str], bytes] | None = None,
    ) -> None:
        self._token = token
        self._timeout_seconds = timeout_seconds
        self._request_json_override = request_json
        self._request_bytes_override = request_bytes
        self._content_cache: dict[str, str | None] = {}
        self._rate_limit_remaining: int | None = None
        self._source_rate_limited = False

    def get_repository_snapshot(self, repository: GitHubRepositoryURL) -> GitHubRepositorySnapshot:
        if not is_valid_github_repository_identity(repository.owner, repository.repository):
            raise GitHubRepositoryIdentityError("GitHub repository identity is not normalized")
        prefix = f"{self.api_base_url}/repos/{repository.owner}/{repository.repository}"
        metadata = self._object(self._get_json(prefix), "repository metadata")
        default_branch = self._string(metadata.get("default_branch"), "default_branch")
        branch = self._object(self._get_json(f"{prefix}/branches/{default_branch}"), "branch")
        commit = self._object(branch.get("commit"), "branch commit")
        commit_sha = self._string(commit.get("sha"), "branch commit sha")
        tree = self._object(self._get_json(f"{prefix}/git/trees/{commit_sha}?recursive=1"), "git tree")
        file_tree = self._tree_paths(tree)
        manifest_paths, warnings = limit_discovered_manifest_paths(
            tuple(path for path in file_tree if _manifest_path(path))
        )
        source_paths = _prioritize_source_paths(file_tree)[:MAX_SOURCE_FILES]
        archive_contents = self._archive_contents(
            prefix, commit_sha, {*manifest_paths, *source_paths, *_readme_paths(file_tree)}
        )
        contents = {path: archive_contents[path] for path in manifest_paths if path in archive_contents}
        manifests, manifest_warnings = _normalized_manifests(
            {"manifest_contents": contents}, manifest_paths, warnings
        )
        languages = self._object(self._get_json(f"{prefix}/languages"), "languages")
        readme_text = next((archive_contents[path] for path in _readme_paths(file_tree) if path in archive_contents), None)
        source_files = tuple((path, archive_contents[path]) for path in source_paths if path in archive_contents)
        return GitHubRepositorySnapshot(
            canonical_url=repository.canonical_url,
            repository_name=repository.repository,
            owner=repository.owner,
            description=self._optional_string(metadata.get("description"), "description"),
            default_branch=default_branch,
            is_public=not self._boolean(metadata.get("private"), "private"),
            is_archived=self._boolean(metadata.get("archived"), "archived"),
            languages=tuple(sorted(key for key in languages if isinstance(key, str)))[:MAX_LANGUAGES],
            file_tree=file_tree,
            readme_text=readme_text,
            manifest_paths=manifest_paths,
            normalized_manifests=manifests,
            manifest_warnings=manifest_warnings,
            source_files=source_files,
            is_demo=False,
            schema_version=GITHUB_SNAPSHOT_SCHEMA_VERSION,
        )

    def _get_json(self, url: str) -> object:
        if self._request_json_override is not None:
            return self._request_json_override(url)
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "BeyondResume"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        try:
            with urlopen(Request(url, headers=headers), timeout=self._timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
                _log_github_request(url, response.status, response.headers, None)
                self._record_rate_limit(response.headers)
                return payload
        except HTTPError as error:
            _log_github_request(url, error.code, error.headers, error)
            self._record_rate_limit(error.headers)
            if error.code == 404:
                raise GitHubRepositoryNotFoundError("GitHub repository was not found") from error
            if error.code == 401:
                raise GitHubAuthenticationError("GitHub authentication failed") from error
            if error.code == 429 or (error.code == 403 and (error.headers.get("X-RateLimit-Remaining") == "0" or error.headers.get("Retry-After"))):
                raise GitHubRateLimitError("GitHub rate limit is exhausted") from error
            raise GitHubProviderError(f"GitHub API returned HTTP {error.code}") from error
        except (URLError, OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            _log_github_request(url, None, None, error)
            raise GitHubProviderError("GitHub API request failed") from error

    def _contents_for_path(self, prefix: str, path: str, commit_sha: str) -> str | None:
        if path in self._content_cache:
            return self._content_cache[path]
        encoded_path = quote(path, safe="/")
        encoded_ref = quote(commit_sha, safe="")
        content = self._optional_contents(f"{prefix}/contents/{encoded_path}?ref={encoded_ref}")
        self._content_cache[path] = content
        return content

    def _archive_contents(self, prefix: str, commit_sha: str, paths: set[str]) -> dict[str, str]:
        archive_url = f"{prefix}/tarball/{quote(commit_sha, safe='')}"
        archive = self._get_bytes(archive_url)
        result: dict[str, str] = {}
        try:
            with tarfile.open(fileobj=BytesIO(archive), mode="r:gz") as tar:
                for member in tar:
                    if not member.isfile() or member.size > MAX_SOURCE_FILE_BYTES:
                        continue
                    path = member.name.split("/", 1)[-1] if "/" in member.name else ""
                    if path not in paths:
                        continue
                    handle = tar.extractfile(member)
                    if handle is None:
                        continue
                    try:
                        result[path] = handle.read().decode("utf-8")
                    except UnicodeDecodeError:
                        continue
        except (tarfile.TarError, OSError) as error:
            raise GitHubProviderError("GitHub archive is invalid") from error
        return result

    def _get_bytes(self, url: str) -> bytes:
        if self._request_bytes_override is not None:
            return self._request_bytes_override(url)
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "BeyondResume"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        try:
            with urlopen(Request(url, headers=headers), timeout=self._timeout_seconds) as response:
                chunks: list[bytes] = []
                size = 0
                while chunk := response.read(64 * 1024):
                    size += len(chunk)
                    if size > MAX_ARCHIVE_BYTES:
                        raise GitHubProviderError("GitHub archive exceeds size limit")
                    chunks.append(chunk)
                _log_github_request(url, response.status, response.headers, None)
                return b"".join(chunks)
        except HTTPError as error:
            _log_github_request(url, error.code, error.headers, error)
            raise GitHubProviderError(f"GitHub archive request returned HTTP {error.code}") from error
        except (URLError, OSError) as error:
            _log_github_request(url, None, None, error)
            raise GitHubProviderError("GitHub archive request failed") from error

    def _source_files(
        self, prefix: str, file_tree: tuple[str, ...], commit_sha: str
    ) -> tuple[tuple[str, str], ...]:
        files: list[tuple[str, str]] = []
        for path in _prioritize_source_paths(file_tree)[: self._source_request_budget()]:
            try:
                content = self._contents_for_path(prefix, path, commit_sha)
            except GitHubRateLimitError:
                self._source_rate_limited = True
                logger.warning("github_source_scan_degraded", extra={"reason": "rate_limit"})
                break
            if content is not None and len(content.encode("utf-8")) <= MAX_SOURCE_FILE_BYTES:
                files.append((path, content))
        return tuple(files)

    def _source_request_budget(self) -> int:
        if self._token:
            return MAX_SOURCE_FILES
        if self._rate_limit_remaining is None:
            return MAX_ANONYMOUS_SOURCE_FILES
        return min(
            MAX_ANONYMOUS_SOURCE_FILES,
            max(self._rate_limit_remaining - SOURCE_REQUEST_RESERVE, 0),
        )

    def _record_rate_limit(self, headers: object) -> None:
        value = getattr(headers, "get", lambda _name: None)("X-RateLimit-Remaining")
        try:
            self._rate_limit_remaining = int(value) if value is not None else None
        except (TypeError, ValueError):
            self._rate_limit_remaining = None

    def _optional_contents(self, url: str) -> str | None:
        try:
            payload = self._object(self._get_json(url), "contents")
        except GitHubRepositoryNotFoundError:
            return None
        content, encoding = payload.get("content"), payload.get("encoding")
        if not isinstance(content, str) or encoding != "base64":
            return None
        try:
            return base64.b64decode(content, validate=False).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return None

    @staticmethod
    def _object(value: object, field: str) -> dict[str, object]:
        if not isinstance(value, dict):
            raise GitHubProviderError(f"GitHub API {field} response is invalid")
        return value

    @staticmethod
    def _string(value: object, field: str) -> str:
        if not isinstance(value, str) or not value:
            raise GitHubProviderError(f"GitHub API {field} response is invalid")
        return value

    @staticmethod
    def _optional_string(value: object, field: str) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise GitHubProviderError(f"GitHub API {field} response is invalid")
        return value

    @staticmethod
    def _boolean(value: object, field: str) -> bool:
        if not isinstance(value, bool):
            raise GitHubProviderError(f"GitHub API {field} response is invalid")
        return value

    @staticmethod
    def _tree_paths(tree: dict[str, object]) -> tuple[str, ...]:
        records = tree.get("tree")
        if not isinstance(records, list):
            raise GitHubProviderError("GitHub API git tree response is invalid")
        paths = [record.get("path") for record in records if isinstance(record, dict) and record.get("type") == "blob"]
        if any(not isinstance(path, str) or not _is_safe_repository_path(path) for path in paths):
            raise GitHubProviderError("GitHub API git tree contains an invalid path")
        return tuple(sorted(paths)[:MAX_FILE_TREE_PATHS])


def _log_github_request(
    url: str,
    status: int | None,
    headers: object,
    error: BaseException | None,
) -> None:
    """Log request diagnostics without exposing credentials or file contents."""
    parts = urlsplit(url).path.strip("/").split("/")
    owner = parts[1] if len(parts) >= 3 and parts[0] == "repos" else None
    repository = parts[2] if len(parts) >= 3 and parts[0] == "repos" else None
    category = "/".join(parts[3:4]) or "repository"
    get_header = getattr(headers, "get", lambda _name: None)
    logger.info(
        "github_api_request",
        extra={
            "operation": "get_repository_snapshot",
            "owner": owner,
            "repository": repository,
            "endpoint_category": category,
            "response_status": status,
            "rate_limit_limit": get_header("X-RateLimit-Limit"),
            "rate_limit_remaining": get_header("X-RateLimit-Remaining"),
            "rate_limit_reset": get_header("X-RateLimit-Reset"),
            "rate_limit_resource": get_header("X-RateLimit-Resource"),
            "exception_class": type(error).__name__ if error is not None else None,
        },
    )


def _prioritize_manifest_paths(paths: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(paths, key=lambda path: (path.count("/"), path)))


def _prioritize_source_paths(paths: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        sorted(
            (
                path
                for path in paths
                if is_analyzable_source_path(path) and not _manifest_path(path)
            ),
            key=lambda path: (_source_path_priority(path), path),
        )
    )


def _readme_paths(paths: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(path for path in paths if path.rsplit("/", 1)[-1].lower().startswith("readme")))


def _source_path_priority(path: str) -> int:
    lower_path = path.lower()
    name = lower_path.rsplit("/", 1)[-1]
    if (
        lower_path.startswith(".github/workflows/")
        or name in CONFIG_FILENAMES
        or is_test_path(path)
    ):
        return 0
    if lower_path.startswith(("src/", "app/", "backend/", "frontend/", "server/", "client/", "packages/")):
        return 1
    if name in {"main.py", "main.ts", "main.tsx", "app.py", "app.ts", "app.tsx", "index.js", "index.ts", "index.tsx"}:
        return 2
    return 3


def _manifest_path(path: str) -> bool:
    return path.rsplit("/", 1)[-1] in {
        "package.json", "pyproject.toml", "requirements.txt", "pom.xml", "go.mod", "Cargo.toml", "composer.json", "Gemfile"
    } or path.lower().endswith(".csproj")


class DemoGitHubProvider:
    """Read deterministic repository snapshots from local JSON fixtures only."""

    def __init__(self, fixture_directory: Path | None = None) -> None:
        self._fixture_directory = fixture_directory or Path(__file__).with_name("fixtures")

    def get_repository_snapshot(self, repository: GitHubRepositoryURL) -> GitHubRepositorySnapshot:
        if not is_valid_github_repository_identity(repository.owner, repository.repository):
            raise GitHubRepositoryIdentityError("GitHub repository identity is not normalized")
        expected_url = f"https://github.com/{repository.owner}/{repository.repository}"
        if repository.canonical_url != expected_url:
            raise GitHubRepositoryIdentityError(
                "GitHub repository canonical URL does not match identity"
            )

        fixture_path = self._fixture_path(repository)
        try:
            raw_fixture = fixture_path.read_text(encoding="utf-8")
        except FileNotFoundError as error:
            raise GitHubRepositoryNotFoundError(
                "GitHub repository fixture was not found"
            ) from error
        except OSError as error:
            raise GitHubFixtureError("GitHub repository fixture could not be read") from error

        try:
            fixture = json.loads(raw_fixture)
        except json.JSONDecodeError as error:
            raise GitHubFixtureError("GitHub repository fixture is malformed") from error

        return _snapshot_from_fixture(fixture, repository)

    def _fixture_path(self, repository: GitHubRepositoryURL) -> Path:
        fixture_name = f"{repository.owner}--{repository.repository}.json"
        fixture_directory = self._fixture_directory.resolve()
        fixture_path = (fixture_directory / fixture_name).resolve()
        if fixture_path.parent != fixture_directory:
            raise GitHubRepositoryIdentityError("GitHub repository fixture path is invalid")
        return fixture_path


def _snapshot_from_fixture(
    fixture: object, repository: GitHubRepositoryURL
) -> GitHubRepositorySnapshot:
    if not isinstance(fixture, dict) or not all(isinstance(key, str) for key in fixture):
        raise GitHubFixtureError("GitHub repository fixture must be an object")

    allowed_fields = {
        "canonical_url",
        "repository_name",
        "owner",
        "description",
        "default_branch",
        "is_public",
        "is_archived",
        "languages",
        "file_tree",
        "readme_text",
        "manifest_paths",
        "manifest_contents",
        "source_files",
    }
    required_fields = {
        "canonical_url",
        "repository_name",
        "owner",
        "is_public",
        "languages",
        "file_tree",
        "manifest_paths",
    }
    if set(fixture) - allowed_fields or required_fields - set(fixture):
        raise GitHubFixtureError("GitHub repository fixture fields are invalid")

    expected_url = f"https://github.com/{repository.owner}/{repository.repository}"
    canonical_url = _required_string(fixture, "canonical_url")
    repository_name = _required_string(fixture, "repository_name")
    owner = _required_string(fixture, "owner")
    if (
        canonical_url != expected_url
        or repository_name != repository.repository
        or owner != repository.owner
    ):
        raise GitHubFixtureError("GitHub repository fixture identity does not match request")

    description = _optional_string(fixture, "description")
    default_branch = _optional_string(fixture, "default_branch")
    readme_text = _optional_string(fixture, "readme_text")
    if readme_text is not None and len(readme_text) > MAX_README_CHARS:
        raise GitHubFixtureError("GitHub repository fixture README is too large")

    is_public = fixture["is_public"]
    is_archived = fixture.get("is_archived")
    if not isinstance(is_public, bool) or (
        is_archived is not None and not isinstance(is_archived, bool)
    ):
        raise GitHubFixtureError("GitHub repository fixture visibility fields are invalid")

    languages = _string_tuple(fixture, "languages", MAX_LANGUAGES)
    file_tree = _path_tuple(fixture, "file_tree", MAX_FILE_TREE_PATHS)
    # §17.6 bounds discovered manifest paths before persistence.
    discovered_manifest_paths = _path_tuple(fixture, "manifest_paths", MAX_FILE_TREE_PATHS)
    if not set(discovered_manifest_paths).issubset(file_tree):
        raise GitHubFixtureError("GitHub repository fixture manifest paths must exist in file tree")
    manifest_paths, limit_warnings = limit_discovered_manifest_paths(discovered_manifest_paths)

    manifests, warnings = _normalized_manifests(fixture, manifest_paths, limit_warnings)
    source_files = _source_files(fixture, file_tree)
    return GitHubRepositorySnapshot(
        canonical_url=canonical_url,
        repository_name=repository_name,
        owner=owner,
        description=description,
        default_branch=default_branch,
        is_public=is_public,
        is_archived=is_archived,
        languages=languages,
        file_tree=file_tree,
        readme_text=readme_text,
        manifest_paths=manifest_paths,
        normalized_manifests=manifests,
        manifest_warnings=warnings,
        source_files=source_files,
        is_demo=True,
        schema_version=GITHUB_SNAPSHOT_SCHEMA_VERSION,
    )


def _normalized_manifests(
    fixture: dict[str, object],
    manifest_paths: tuple[str, ...],
    limit_warnings: tuple[GitHubManifestWarning, ...],
) -> tuple[tuple[GitHubNormalizedManifest, ...], tuple[GitHubManifestWarning, ...]]:
    contents = fixture.get("manifest_contents", {})
    if not isinstance(contents, dict) or not all(isinstance(path, str) for path in contents):
        raise GitHubFixtureError("GitHub repository fixture manifest contents are invalid")
    try:
        return normalize_fixture_manifests(
            manifest_paths, contents, initial_warnings=limit_warnings
        )
    except InvalidNormalizedDependencyError:
        raise
    except GitHubManifestValidationError as error:
        raise GitHubFixtureError("GitHub repository fixture manifests are invalid") from error


def _required_string(fixture: dict[str, object], field: str) -> str:
    value = fixture.get(field)
    if not isinstance(value, str) or not value:
        raise GitHubFixtureError(f"GitHub repository fixture field {field} is invalid")
    return value


def _optional_string(fixture: dict[str, object], field: str) -> str | None:
    value = fixture.get(field)
    if value is not None and not isinstance(value, str):
        raise GitHubFixtureError(f"GitHub repository fixture field {field} is invalid")
    return value


def _string_tuple(fixture: dict[str, object], field: str, maximum_size: int) -> tuple[str, ...]:
    value = fixture[field]
    if not isinstance(value, list) or len(value) > maximum_size:
        raise GitHubFixtureError(f"GitHub repository fixture field {field} is invalid")
    if any(not isinstance(item, str) or not item for item in value):
        raise GitHubFixtureError(f"GitHub repository fixture field {field} is invalid")
    return tuple(value)


def _path_tuple(fixture: dict[str, object], field: str, maximum_size: int) -> tuple[str, ...]:
    paths = _string_tuple(fixture, field, maximum_size)
    if any(not _is_safe_repository_path(path) for path in paths):
        raise GitHubFixtureError(f"GitHub repository fixture field {field} contains unsafe path")
    return paths


def _source_files(fixture: dict[str, object], file_tree: tuple[str, ...]) -> tuple[tuple[str, str], ...]:
    value = fixture.get("source_files", {})
    if not isinstance(value, dict) or not all(isinstance(path, str) and isinstance(content, str) for path, content in value.items()):
        raise GitHubFixtureError("GitHub repository fixture source files are invalid")
    if len(value) > MAX_SOURCE_FILES or any(path not in file_tree or len(content.encode("utf-8")) > MAX_SOURCE_FILE_BYTES for path, content in value.items()):
        raise GitHubFixtureError("GitHub repository fixture source files exceed bounds")
    if any(not is_analyzable_source_path(path) for path in value):
        raise GitHubFixtureError("GitHub repository fixture source file path is invalid")
    return tuple(sorted(value.items()))


def _is_safe_repository_path(path: str) -> bool:
    return not (
        path.startswith("/")
        or "\\" in path
        or any(part in {"", ".", ".."} for part in path.split("/"))
    )
