from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Mapping

from app.integrations.github import (
    MAX_FILE_TREE_PATHS,
    MAX_LANGUAGES,
    MAX_MANIFEST_PATHS,
    MAX_README_CHARS,
    GitHubRepositorySnapshot,
)


class GitHubSnapshotValidationError(ValueError):
    """Raised when a snapshot cannot be persisted safely."""


@dataclass(frozen=True, slots=True)
class CanonicalGitHubRepositorySnapshot:
    payload: Mapping[str, object]
    canonical_json: str
    checksum: str


def canonicalize_github_repository_snapshot(
    snapshot: GitHubRepositorySnapshot,
) -> CanonicalGitHubRepositorySnapshot:
    _validate_bounds(snapshot)
    payload = {
        "canonical_url": snapshot.canonical_url,
        "default_branch": snapshot.default_branch,
        "description": snapshot.description,
        "is_archived": snapshot.is_archived,
        "is_demo": snapshot.is_demo,
        "is_public": snapshot.is_public,
        "languages": list(snapshot.languages),
        "manifest_paths": list(snapshot.manifest_paths),
        "owner": snapshot.owner,
        "readme_text": snapshot.readme_text,
        "repository_name": snapshot.repository_name,
        "tree_paths": list(snapshot.file_tree),
    }
    canonical_json = json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    )
    checksum = sha256(canonical_json.encode("utf-8")).hexdigest()
    immutable_payload = MappingProxyType(
        {
            **payload,
            "languages": tuple(snapshot.languages),
            "manifest_paths": tuple(snapshot.manifest_paths),
            "tree_paths": tuple(snapshot.file_tree),
        }
    )
    return CanonicalGitHubRepositorySnapshot(
        payload=immutable_payload,
        canonical_json=canonical_json,
        checksum=checksum,
    )


def _validate_bounds(snapshot: GitHubRepositorySnapshot) -> None:
    if (
        len(snapshot.languages) > MAX_LANGUAGES
        or len(snapshot.file_tree) > MAX_FILE_TREE_PATHS
        or len(snapshot.manifest_paths) > MAX_MANIFEST_PATHS
        or (snapshot.readme_text is not None and len(snapshot.readme_text) > MAX_README_CHARS)
    ):
        raise GitHubSnapshotValidationError("GitHub repository snapshot exceeds persistence bounds")
