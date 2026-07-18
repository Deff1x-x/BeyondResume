from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.github import GitHubProvider
from app.models.evidence_unit import EvidenceUnit
from app.models.github_repository import GitHubRepository
from app.models.github_repository_snapshot import GitHubRepositorySnapshot
from app.services.github_evidence import (
    GitHubEvidenceGenerationResult,
    generate_github_repository_evidence,
)
from app.services.github_scan import (
    GitHubRepositorySourceNotFoundError,
    fetch_github_repository_snapshot,
)
from app.services.github_snapshot import (
    GitHubRepositorySnapshotPersistenceResult,
    persist_github_repository_snapshot,
)


@dataclass(frozen=True, slots=True)
class GitHubRepositoryScanResult:
    repository: GitHubRepository
    persisted_snapshot: GitHubRepositorySnapshot
    evidence_unit: EvidenceUnit
    snapshot_created: bool
    snapshot_changed: bool
    evidence_created: bool
    evidence_changed: bool


def run_github_repository_scan(
    session: Session, candidate_id: UUID, provider: GitHubProvider
) -> GitHubRepositoryScanResult:
    provider_snapshot = fetch_github_repository_snapshot(session, candidate_id, provider)
    repository = session.execute(
        select(GitHubRepository).where(GitHubRepository.candidate_id == candidate_id)
    ).scalar_one_or_none()
    if repository is None:
        raise GitHubRepositorySourceNotFoundError

    persistence_result = persist_github_repository_snapshot(session, repository, provider_snapshot)
    evidence_result = generate_github_repository_evidence(session, candidate_id)
    return _result(repository, persistence_result, evidence_result)


def _result(
    repository: GitHubRepository,
    persistence_result: GitHubRepositorySnapshotPersistenceResult,
    evidence_result: GitHubEvidenceGenerationResult,
) -> GitHubRepositoryScanResult:
    return GitHubRepositoryScanResult(
        repository=repository,
        persisted_snapshot=persistence_result.snapshot,
        evidence_unit=evidence_result.evidence_unit,
        snapshot_created=persistence_result.created,
        snapshot_changed=persistence_result.changed,
        evidence_created=evidence_result.created,
        evidence_changed=evidence_result.changed,
    )
