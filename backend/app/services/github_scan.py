from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.github import GitHubProvider, GitHubRepositorySnapshot
from app.models.candidate_profile import CandidateProfile
from app.models.github_repository import GitHubRepository
from app.services.candidate import CandidateProfileNotFoundError
from app.utils.github_url import (
    GitHubRepositoryURL,
    GitHubRepositoryUrlError,
    parse_github_repository_url,
)


class GitHubRepositorySourceNotFoundError(Exception):
    """Raised when a candidate has not connected a GitHub repository source."""


class GitHubSnapshotIdentityMismatchError(Exception):
    """Raised when a provider snapshot does not match the connected repository."""


def fetch_github_repository_snapshot(
    session: Session, candidate_id: UUID, provider: GitHubProvider, repository_id: UUID | None = None
) -> GitHubRepositorySnapshot:
    candidate = session.execute(
        select(CandidateProfile).where(CandidateProfile.id == candidate_id)
    ).scalar_one_or_none()
    if candidate is None:
        raise CandidateProfileNotFoundError

    repository = session.execute(
        select(GitHubRepository).where(
            GitHubRepository.candidate_id == candidate_id,
            *( (GitHubRepository.id == repository_id,) if repository_id is not None else () ),
        )
    ).scalar_one_or_none()
    if repository is None:
        raise GitHubRepositorySourceNotFoundError

    parsed_repository = parse_github_repository_url(repository.repository_url)
    snapshot = provider.get_repository_snapshot(parsed_repository)
    _validate_snapshot_identity(snapshot, parsed_repository)
    return snapshot


def _validate_snapshot_identity(
    snapshot: GitHubRepositorySnapshot, expected_repository: GitHubRepositoryURL
) -> None:
    try:
        parsed_snapshot_url = parse_github_repository_url(snapshot.canonical_url)
    except GitHubRepositoryUrlError as error:
        raise GitHubSnapshotIdentityMismatchError from error

    if (
        snapshot.owner.lower() != expected_repository.owner
        or snapshot.repository_name.lower() != expected_repository.repository
        or parsed_snapshot_url.owner != expected_repository.owner
        or parsed_snapshot_url.repository != expected_repository.repository
        or parsed_snapshot_url.canonical_url != expected_repository.canonical_url
    ):
        raise GitHubSnapshotIdentityMismatchError
