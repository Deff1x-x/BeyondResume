from dataclasses import dataclass
from typing import Any, Mapping

from app.integrations.github import (
    MAX_FILE_TREE_PATHS,
    MAX_LANGUAGES,
    MAX_README_CHARS,
)
from app.utils.github_manifests import MAX_DISCOVERED_MANIFESTS
from app.utils.github_url import GitHubRepositoryUrlError, parse_github_repository_url
from app.utils.github_snapshot import (
    GitHubSnapshotValidationError,
    read_github_repository_snapshot_payload,
)


class GitHubPersistedSnapshotValidationError(ValueError):
    """Raised when a persisted GitHub snapshot payload is not canonical."""


@dataclass(frozen=True, slots=True)
class PersistedGitHubRepositoryPayload:
    canonical_url: str
    owner: str
    repository_name: str
    description: str | None
    is_archived: bool | None
    languages: tuple[str, ...]
    tree_paths: tuple[str, ...]
    readme_text: str | None
    manifest_paths: tuple[str, ...]


_PAYLOAD_FIELDS = frozenset(
    {
        "canonical_url",
        "default_branch",
        "description",
        "is_archived",
        "is_demo",
        "is_public",
        "languages",
        "manifest_paths",
        "owner",
        "readme_text",
        "repository_name",
        "tree_paths",
    }
)
_V2_PAYLOAD_FIELDS = _PAYLOAD_FIELDS | {
    "schema_version",
    "normalized_manifests",
    "manifest_warnings",
}
_V3_PAYLOAD_FIELDS = _V2_PAYLOAD_FIELDS | {"source_files"}


def validate_persisted_github_repository_payload(
    payload: Mapping[str, object],
) -> PersistedGitHubRepositoryPayload:
    if set(payload) not in {_PAYLOAD_FIELDS, _V2_PAYLOAD_FIELDS, _V3_PAYLOAD_FIELDS}:
        raise GitHubPersistedSnapshotValidationError("GitHub snapshot payload fields are invalid")
    try:
        read_github_repository_snapshot_payload(payload)
    except GitHubSnapshotValidationError as error:
        raise GitHubPersistedSnapshotValidationError(
            "GitHub snapshot payload is invalid"
        ) from error

    canonical_url = _string(payload, "canonical_url")
    try:
        parsed_url = parse_github_repository_url(canonical_url)
    except GitHubRepositoryUrlError as error:
        raise GitHubPersistedSnapshotValidationError(
            "GitHub snapshot canonical URL is invalid"
        ) from error

    owner = _string(payload, "owner")
    repository_name = _string(payload, "repository_name")
    if owner != parsed_url.owner or repository_name != parsed_url.repository:
        raise GitHubPersistedSnapshotValidationError("GitHub snapshot identity is invalid")

    _optional_string(payload, "default_branch")
    description = _optional_string(payload, "description")
    readme_text = _optional_string(payload, "readme_text")
    _boolean(payload, "is_public")
    is_archived = _optional_boolean(payload, "is_archived")
    _boolean(payload, "is_demo")
    languages = _string_collection(payload, "languages", MAX_LANGUAGES)
    tree_paths = _string_collection(payload, "tree_paths", MAX_FILE_TREE_PATHS)
    manifest_paths = _string_collection(payload, "manifest_paths", MAX_DISCOVERED_MANIFESTS)
    if readme_text is not None and len(readme_text) > MAX_README_CHARS:
        raise GitHubPersistedSnapshotValidationError("GitHub snapshot README is too large")

    return PersistedGitHubRepositoryPayload(
        canonical_url=canonical_url,
        owner=owner,
        repository_name=repository_name,
        description=description,
        is_archived=is_archived,
        languages=languages,
        tree_paths=tree_paths,
        readme_text=readme_text,
        manifest_paths=manifest_paths,
    )


def _string(payload: Mapping[str, object], field: str) -> str:
    value = payload[field]
    if not isinstance(value, str) or not value:
        raise GitHubPersistedSnapshotValidationError(f"GitHub snapshot field {field} is invalid")
    return value


def _optional_string(payload: Mapping[str, object], field: str) -> str | None:
    value = payload[field]
    if value is not None and not isinstance(value, str):
        raise GitHubPersistedSnapshotValidationError(f"GitHub snapshot field {field} is invalid")
    return value


def _boolean(payload: Mapping[str, object], field: str) -> bool:
    value = payload[field]
    if not isinstance(value, bool):
        raise GitHubPersistedSnapshotValidationError(f"GitHub snapshot field {field} is invalid")
    return value


def _optional_boolean(payload: Mapping[str, object], field: str) -> bool | None:
    value = payload[field]
    if value is not None and not isinstance(value, bool):
        raise GitHubPersistedSnapshotValidationError(f"GitHub snapshot field {field} is invalid")
    return value


def _string_collection(
    payload: Mapping[str, object], field: str, maximum_size: int
) -> tuple[str, ...]:
    value: Any = payload[field]
    if (
        not isinstance(value, list)
        or len(value) > maximum_size
        or any(not isinstance(item, str) or not item for item in value)
    ):
        raise GitHubPersistedSnapshotValidationError(f"GitHub snapshot field {field} is invalid")
    return tuple(value)
