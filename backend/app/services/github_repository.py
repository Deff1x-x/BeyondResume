from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.candidate_profile import CandidateProfile
from app.models.github_repository import GitHubRepository
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
