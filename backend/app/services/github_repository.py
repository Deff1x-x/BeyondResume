from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.candidate_profile import CandidateProfile
from app.models.evidence_skill_link import EvidenceSkillLink
from app.models.evidence_unit import EvidenceUnit
from app.models.github_repository import GitHubRepository
from app.models.github_repository_snapshot import GitHubRepositorySnapshot
from app.services.candidate import CandidateProfileNotFoundError
from app.utils.github_url import parse_github_repository_url


class GitHubRepositoryConflictError(Exception):
    """Raised when a candidate already has a different GitHub repository."""


def connect_github_repository(
    session: Session, candidate_id: UUID, repository_url: str
) -> GitHubRepository:
    normalized_url = parse_github_repository_url(repository_url)
    candidate = session.execute(
        select(CandidateProfile).where(CandidateProfile.id == candidate_id)
    ).scalar_one_or_none()
    if candidate is None:
        raise CandidateProfileNotFoundError

    existing_repository = session.execute(
        select(GitHubRepository).where(GitHubRepository.candidate_id == candidate_id)
    ).scalar_one_or_none()
    if existing_repository is not None:
        if existing_repository.repository_url == normalized_url.canonical_url:
            return existing_repository
        raise GitHubRepositoryConflictError

    repository = GitHubRepository(
        candidate_id=candidate_id,
        repository_url=normalized_url.canonical_url,
    )
    session.add(repository)
    session.flush()
    return repository


def disconnect_github_repository(
    session: Session, candidate_id: UUID, repository_id: UUID
) -> bool:
    """Delete the repository with its snapshot and GitHub-derived evidence.

    Returns False when the repository does not exist or belongs to another candidate.
    The caller owns the transaction boundary; this function only flushes.
    """
    repository = session.execute(
        select(GitHubRepository).where(
            GitHubRepository.id == repository_id,
            GitHubRepository.candidate_id == candidate_id,
        )
    ).scalar_one_or_none()
    if repository is None:
        return False

    evidence_units = (
        session.execute(
            select(EvidenceUnit).where(
                EvidenceUnit.candidate_id == candidate_id,
                EvidenceUnit.source_type == "github_repository",
                EvidenceUnit.source_reference == repository.repository_url,
            )
        )
        .scalars()
        .all()
    )
    for evidence_unit in evidence_units:
        session.execute(
            delete(EvidenceSkillLink).where(
                EvidenceSkillLink.evidence_unit_id == evidence_unit.id
            )
        )
        session.delete(evidence_unit)

    session.execute(
        delete(GitHubRepositorySnapshot).where(
            GitHubRepositorySnapshot.repository_id == repository.id
        )
    )
    session.delete(repository)
    session.flush()
    return True
