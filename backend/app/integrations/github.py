from dataclasses import dataclass
import json
from pathlib import Path
from typing import Final, Protocol

from app.utils.github_manifests import (
    GitHubManifestValidationError,
    GitHubManifestWarning,
    GitHubNormalizedManifest,
    InvalidNormalizedDependencyError,
    limit_discovered_manifest_paths,
    normalize_fixture_manifests,
)

from app.utils.github_url import GitHubRepositoryURL, is_valid_github_repository_identity


MAX_LANGUAGES: Final = 20
MAX_FILE_TREE_PATHS: Final = 500
MAX_README_CHARS: Final = 10_000
GITHUB_SNAPSHOT_SCHEMA_VERSION: Final = 2


class GitHubProviderError(Exception):
    """Base error for GitHub provider failures."""


class GitHubRepositoryNotFoundError(GitHubProviderError):
    """Raised when a requested repository fixture does not exist."""


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


class GitHubProvider(Protocol):
    def get_repository_snapshot(
        self, repository: GitHubRepositoryURL
    ) -> GitHubRepositorySnapshot: ...


def get_github_provider() -> "GitHubProvider":
    """Return the configured snapshot provider.

    The demo provider is currently the only implementation; a live GitHub
    provider plugs in here without changing workers or the HTTP API.
    """
    return DemoGitHubProvider()


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


def _is_safe_repository_path(path: str) -> bool:
    return not (
        path.startswith("/")
        or "\\" in path
        or any(part in {"", ".", ".."} for part in path.split("/"))
    )
