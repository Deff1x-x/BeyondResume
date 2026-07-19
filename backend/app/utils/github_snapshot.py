"""Canonical v2 GitHub snapshot serialization and persisted-payload reading."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Mapping

from app.integrations.github import (
    GITHUB_SNAPSHOT_SCHEMA_VERSION,
    MAX_FILE_TREE_PATHS,
    MAX_LANGUAGES,
    MAX_README_CHARS,
    GitHubRepositorySnapshot,
)
from app.utils.github_manifests import (
    GitHubManifestValidationError,
    GitHubManifestWarning,
    GitHubNormalizedDependency,
    GitHubNormalizedManifest,
    MAX_DISCOVERED_MANIFESTS,
    WARNING_CODES,
    manifest_type,
    normalize_manifest_path,
    thaw_json_value,
)


class GitHubSnapshotValidationError(ValueError):
    """Raised when a snapshot cannot be persisted or read safely."""


class UnsupportedGitHubSnapshotSchemaError(GitHubSnapshotValidationError):
    """Raised for a persisted schema version this application does not understand."""


@dataclass(frozen=True, slots=True)
class CanonicalGitHubRepositorySnapshot:
    payload: Mapping[str, object]
    canonical_json: str
    checksum: str


_V1_FIELDS = frozenset(
    {
        "canonical_url",
        "repository_name",
        "owner",
        "description",
        "default_branch",
        "is_public",
        "is_archived",
        "languages",
        "tree_paths",
        "readme_text",
        "manifest_paths",
        "is_demo",
    }
)
_V2_FIELDS = _V1_FIELDS | {"schema_version", "normalized_manifests", "manifest_warnings"}


def canonicalize_github_repository_snapshot(
    snapshot: GitHubRepositorySnapshot,
) -> CanonicalGitHubRepositorySnapshot:
    if snapshot.schema_version != GITHUB_SNAPSHOT_SCHEMA_VERSION:
        raise UnsupportedGitHubSnapshotSchemaError("provider snapshot schema is unsupported")
    _validate_bounds(snapshot)
    payload = _v2_payload(snapshot)
    canonical_json = json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    )
    return CanonicalGitHubRepositorySnapshot(
        payload=MappingProxyType(_detached_payload(payload)),
        canonical_json=canonical_json,
        checksum=sha256(canonical_json.encode("utf-8")).hexdigest(),
    )


def read_github_repository_snapshot_payload(
    payload: Mapping[str, object],
) -> GitHubRepositorySnapshot:
    """Read a historical v1 or current v2 JSON payload without mutating persistence."""
    if not isinstance(payload, Mapping):
        raise GitHubSnapshotValidationError("persisted snapshot payload must be an object")
    version = payload.get("schema_version", 1)
    if not isinstance(version, int) or isinstance(version, bool) or version not in {1, 2}:
        raise UnsupportedGitHubSnapshotSchemaError("persisted snapshot schema is unsupported")
    required_fields = _V2_FIELDS if version == 2 else _V1_FIELDS
    if set(payload) != required_fields:
        raise GitHubSnapshotValidationError("persisted snapshot fields are invalid")
    try:
        manifest_paths = _string_array(payload, "manifest_paths")
        manifests = (
            _read_manifests(payload["normalized_manifests"], manifest_paths) if version == 2 else ()
        )
        warnings = _read_warnings(payload["manifest_warnings"]) if version == 2 else ()
        result = GitHubRepositorySnapshot(
            canonical_url=_string(payload, "canonical_url"),
            repository_name=_string(payload, "repository_name"),
            owner=_string(payload, "owner"),
            description=_optional_string(payload, "description"),
            default_branch=_optional_string(payload, "default_branch"),
            is_public=_boolean(payload, "is_public"),
            is_archived=_optional_boolean(payload, "is_archived"),
            languages=_string_array(payload, "languages"),
            file_tree=_string_array(payload, "tree_paths"),
            readme_text=_optional_string(payload, "readme_text"),
            manifest_paths=manifest_paths,
            is_demo=_boolean(payload, "is_demo"),
            schema_version=version,
            normalized_manifests=manifests,
            manifest_warnings=warnings,
        )
        _validate_bounds(result)
        return result
    except (KeyError, TypeError, GitHubManifestValidationError) as error:
        raise GitHubSnapshotValidationError("persisted snapshot payload is invalid") from error


def _v2_payload(snapshot: GitHubRepositorySnapshot) -> dict[str, object]:
    manifests = sorted(snapshot.normalized_manifests, key=lambda value: (value.path, value.kind))
    warnings = sorted(
        snapshot.manifest_warnings, key=lambda value: (value.path, value.code, value.detail or "")
    )
    return {
        "schema_version": GITHUB_SNAPSHOT_SCHEMA_VERSION,
        "canonical_url": snapshot.canonical_url,
        "repository_name": snapshot.repository_name,
        "owner": snapshot.owner,
        "description": snapshot.description,
        "default_branch": snapshot.default_branch,
        "is_public": snapshot.is_public,
        "is_archived": snapshot.is_archived,
        "is_demo": snapshot.is_demo,
        "languages": sorted(snapshot.languages),
        "tree_paths": sorted(snapshot.file_tree),
        "readme_text": snapshot.readme_text,
        "manifest_paths": sorted(snapshot.manifest_paths),
        "normalized_manifests": [_manifest_payload(value) for value in manifests],
        "manifest_warnings": [_warning_payload(value) for value in warnings],
    }


def _manifest_payload(value: GitHubNormalizedManifest) -> dict[str, object]:
    _validate_manifest(value)
    return {
        "path": value.path,
        "kind": value.kind,
        "ecosystem": value.ecosystem,
        "dependencies": [
            {
                "name": dependency.name,
                "section": dependency.section,
                "metadata": thaw_json_value(dependency.metadata),
            }
            for dependency in sorted(value.dependencies, key=_dependency_sort_key)
        ],
    }


def _warning_payload(value: GitHubManifestWarning) -> dict[str, object]:
    if value.code not in WARNING_CODES or normalize_manifest_path(value.path) != value.path:
        raise GitHubSnapshotValidationError("snapshot warning is invalid")
    return {"path": value.path, "kind": value.kind, "code": value.code, "detail": value.detail}


def _detached_payload(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return {key: _detached_value(item) for key, item in value.items()}
    raise TypeError("snapshot payload must be an object")


def _detached_value(value: object) -> object:
    if isinstance(value, dict):
        return {key: _detached_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_detached_value(item) for item in value]
    return value


def _read_manifests(
    value: object, manifest_paths: tuple[str, ...]
) -> tuple[GitHubNormalizedManifest, ...]:
    if not isinstance(value, list):
        raise TypeError
    manifests: list[GitHubNormalizedManifest] = []
    for item in value:
        if not isinstance(item, dict) or set(item) != {"path", "kind", "ecosystem", "dependencies"}:
            raise TypeError
        path = _string(item, "path")
        kind = _string(item, "kind")
        ecosystem = _string(item, "ecosystem")
        if (
            path not in manifest_paths
            or normalize_manifest_path(path) != path
            or manifest_type(path) != (kind, ecosystem)
        ):
            raise TypeError
        dependencies_value = item["dependencies"]
        if not isinstance(dependencies_value, list):
            raise TypeError
        dependencies = tuple(_read_dependency(dependency) for dependency in dependencies_value)
        manifest = GitHubNormalizedManifest(path, kind, ecosystem, dependencies)
        _validate_manifest(manifest)
        manifests.append(manifest)
    return tuple(manifests)


def _read_dependency(value: object) -> GitHubNormalizedDependency:
    if not isinstance(value, dict) or set(value) != {"name", "section", "metadata"}:
        raise TypeError
    name = _string(value, "name")
    section = _optional_string(value, "section")
    metadata = value["metadata"]
    if not isinstance(metadata, dict) or not all(isinstance(key, str) for key in metadata):
        raise TypeError
    return GitHubNormalizedDependency(name, section, metadata)


def _read_warnings(value: object) -> tuple[GitHubManifestWarning, ...]:
    if not isinstance(value, list):
        raise TypeError
    result: list[GitHubManifestWarning] = []
    for item in value:
        if not isinstance(item, dict) or set(item) != {"path", "kind", "code", "detail"}:
            raise TypeError
        path = _string(item, "path")
        kind = _optional_string(item, "kind")
        code = _string(item, "code")
        detail = _optional_string(item, "detail")
        if normalize_manifest_path(path) != path or code not in WARNING_CODES:
            raise TypeError
        result.append(GitHubManifestWarning(path, kind, code, detail))
    return tuple(result)


def _string(payload: Mapping[str, object], key: str) -> str:
    value = payload[key]
    if not isinstance(value, str):
        raise TypeError
    return value


def _optional_string(payload: Mapping[str, object], key: str) -> str | None:
    value = payload[key]
    if value is not None and not isinstance(value, str):
        raise TypeError
    return value


def _boolean(payload: Mapping[str, object], key: str) -> bool:
    value = payload[key]
    if not isinstance(value, bool):
        raise TypeError
    return value


def _optional_boolean(payload: Mapping[str, object], key: str) -> bool | None:
    value = payload[key]
    if value is not None and not isinstance(value, bool):
        raise TypeError
    return value


def _string_array(payload: Mapping[str, object], key: str) -> tuple[str, ...]:
    value = payload[key]
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise TypeError
    return tuple(value)


def _dependency_sort_key(value: GitHubNormalizedDependency) -> tuple[str, str, str]:
    return (
        value.name,
        value.section or "",
        json.dumps(
            thaw_json_value(value.metadata),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        ),
    )


def _validate_manifest(manifest: GitHubNormalizedManifest) -> None:
    if normalize_manifest_path(manifest.path) != manifest.path or manifest_type(manifest.path) != (
        manifest.kind,
        manifest.ecosystem,
    ):
        raise GitHubSnapshotValidationError("normalized manifest is invalid")
    allowed_metadata = {
        "package_json": frozenset(),
        "pyproject_toml": frozenset({"group"}),
        "requirements_txt": frozenset(),
        "pom_xml": frozenset({"group_id", "artifact_id"}),
        "go_mod": frozenset({"indirect"}),
        "cargo_toml": frozenset({"alias", "target"}),
        "composer_json": frozenset(),
        "gemfile": frozenset(),
        "csproj": frozenset(),
    }[manifest.kind]
    for dependency in manifest.dependencies:
        if (
            not dependency.name
            or len(dependency.name) > 255
            or set(dependency.metadata) != allowed_metadata
            or not _metadata_value_types_are_valid(manifest.kind, dependency.metadata)
        ):
            raise GitHubSnapshotValidationError("normalized dependency is invalid")


def _metadata_value_types_are_valid(kind: str, metadata: Mapping[str, object]) -> bool:
    if kind == "pyproject_toml":
        return metadata["group"] is None or isinstance(metadata["group"], str)
    if kind == "pom_xml":
        return all(isinstance(metadata[key], str) and metadata[key] for key in metadata)
    if kind == "go_mod":
        return isinstance(metadata["indirect"], bool)
    if kind == "cargo_toml":
        return all(metadata[key] is None or isinstance(metadata[key], str) for key in metadata)
    return True


def _validate_bounds(snapshot: GitHubRepositorySnapshot) -> None:
    if (
        len(snapshot.languages) > MAX_LANGUAGES
        or len(snapshot.file_tree) > MAX_FILE_TREE_PATHS
        or len(snapshot.manifest_paths) > MAX_DISCOVERED_MANIFESTS
        or (snapshot.readme_text is not None and len(snapshot.readme_text) > MAX_README_CHARS)
    ):
        raise GitHubSnapshotValidationError("GitHub repository snapshot exceeds persistence bounds")
