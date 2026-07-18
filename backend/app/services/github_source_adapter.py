from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.github import GitHubProvider, GitHubRepositorySnapshot
from app.models.github_repository import GitHubRepository
from app.services.github_evidence import (
    GitHubEvidenceGenerationResult,
    generate_github_repository_evidence,
)
from app.services.github_full_scan import GitHubRepositoryScanResult, run_github_repository_scan
from app.services.github_scan import (
    GitHubRepositorySourceNotFoundError,
    fetch_github_repository_snapshot,
)
from app.services.github_snapshot import (
    GitHubRepositorySnapshotPersistenceResult,
    persist_github_repository_snapshot,
)


class GitHubSourceAdapter:
    source_type = "github_repository"

    def __init__(self, provider: GitHubProvider) -> None:
        self._provider = provider

    def fetch(self, session: Session, candidate_id: UUID) -> GitHubRepositorySnapshot:
        return fetch_github_repository_snapshot(session, candidate_id, self._provider)

    def normalize(self, snapshot: GitHubRepositorySnapshot) -> GitHubRepositorySnapshot:
        return snapshot

    def persist_snapshot(
        self, session: Session, candidate_id: UUID, snapshot: GitHubRepositorySnapshot
    ) -> GitHubRepositorySnapshotPersistenceResult:
        repository = session.execute(
            select(GitHubRepository).where(GitHubRepository.candidate_id == candidate_id)
        ).scalar_one_or_none()
        if repository is None:
            raise GitHubRepositorySourceNotFoundError
        return persist_github_repository_snapshot(session, repository, snapshot)

    def generate_evidence(
        self, session: Session, candidate_id: UUID
    ) -> GitHubEvidenceGenerationResult:
        return generate_github_repository_evidence(session, candidate_id)

    def run_scan(self, session: Session, candidate_id: UUID) -> GitHubRepositoryScanResult:
        return run_github_repository_scan(session, candidate_id, self._provider)
