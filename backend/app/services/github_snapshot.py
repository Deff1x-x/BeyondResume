from dataclasses import dataclass
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.github import GitHubRepositorySnapshot as ProviderGitHubRepositorySnapshot
from app.models.github_repository import GitHubRepository
from app.models.github_repository_snapshot import GitHubRepositorySnapshot
from app.services.github_scan import _validate_snapshot_identity
from app.utils.github_snapshot import canonicalize_github_repository_snapshot
from app.utils.github_url import parse_github_repository_url


@dataclass(frozen=True, slots=True)
class GitHubRepositorySnapshotPersistenceResult:
    snapshot: GitHubRepositorySnapshot
    created: bool
    changed: bool


def persist_github_repository_snapshot(
    session: Session,
    github_repository: GitHubRepository,
    snapshot: ProviderGitHubRepositorySnapshot,
) -> GitHubRepositorySnapshotPersistenceResult:
    parsed_repository = parse_github_repository_url(github_repository.repository_url)
    _validate_snapshot_identity(snapshot, parsed_repository)
    canonical_snapshot = canonicalize_github_repository_snapshot(snapshot)
    persisted_snapshot = session.execute(
        select(GitHubRepositorySnapshot).where(
            GitHubRepositorySnapshot.repository_id == github_repository.id
        )
    ).scalar_one_or_none()

    if persisted_snapshot is None:
        persisted_snapshot = GitHubRepositorySnapshot(
            repository_id=github_repository.id,
            checksum=canonical_snapshot.checksum,
            payload=json.loads(canonical_snapshot.canonical_json),
        )
        session.add(persisted_snapshot)
        session.flush()
        return GitHubRepositorySnapshotPersistenceResult(
            snapshot=persisted_snapshot, created=True, changed=True
        )

    if persisted_snapshot.checksum == canonical_snapshot.checksum:
        return GitHubRepositorySnapshotPersistenceResult(
            snapshot=persisted_snapshot, created=False, changed=False
        )

    persisted_snapshot.checksum = canonical_snapshot.checksum
    persisted_snapshot.payload = json.loads(canonical_snapshot.canonical_json)
    session.flush()
    return GitHubRepositorySnapshotPersistenceResult(
        snapshot=persisted_snapshot, created=False, changed=True
    )
