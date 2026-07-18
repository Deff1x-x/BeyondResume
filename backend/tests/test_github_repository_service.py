from unittest.mock import Mock
from uuid import UUID, uuid4
import socket

import pytest
from sqlalchemy import UniqueConstraint
from sqlalchemy.exc import IntegrityError

from app.models.candidate_profile import CandidateProfile, OnboardingStatus
from app.models.evidence_unit import EvidenceUnit
from app.models.github_repository import GitHubRepository
from app.services.candidate import CandidateProfileNotFoundError
from app.services.github_repository import (
    GitHubRepositoryConflictError,
    connect_github_repository,
)
from app.utils.github_url import GitHubRepositoryUrlError


def make_candidate(candidate_id: UUID | None = None) -> CandidateProfile:
    return CandidateProfile(
        id=candidate_id or uuid4(),
        user_id=uuid4(),
        display_name="Demo Candidate",
        onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
    )


def make_session(candidate: CandidateProfile | None, repository: GitHubRepository | None) -> Mock:
    session = Mock()
    candidate_result = Mock()
    candidate_result.scalar_one_or_none.return_value = candidate
    repository_result = Mock()
    repository_result.scalar_one_or_none.return_value = repository
    session.execute.side_effect = [candidate_result, repository_result]
    return session


@pytest.mark.parametrize(
    ("repository_url", "canonical_url"),
    [
        ("https://github.com/Demo-User/Demo-API", "https://github.com/demo-user/demo-api"),
        ("https://www.github.com/demo-user/demo-api/", "https://github.com/demo-user/demo-api"),
        ("https://github.com/demo-user/demo-api.git", "https://github.com/demo-user/demo-api"),
    ],
)
def test_connect_saves_canonical_repository_url(repository_url: str, canonical_url: str) -> None:
    candidate = make_candidate()
    session = make_session(candidate, None)

    repository = connect_github_repository(session, candidate.id, repository_url)

    assert repository.candidate_id == candidate.id
    assert repository.repository_url == canonical_url
    session.add.assert_called_once_with(repository)
    session.flush.assert_called_once()
    session.commit.assert_not_called()
    session.rollback.assert_not_called()


def test_connect_is_idempotent_for_same_canonical_url() -> None:
    candidate = make_candidate()
    existing_repository = GitHubRepository(
        candidate_id=candidate.id,
        repository_url="https://github.com/demo-user/demo-api",
    )
    session = make_session(candidate, existing_repository)

    repository = connect_github_repository(
        session, candidate.id, "https://www.github.com/Demo-User/Demo-API.git/"
    )

    assert repository is existing_repository
    assert existing_repository.repository_url == "https://github.com/demo-user/demo-api"
    session.add.assert_not_called()
    session.flush.assert_not_called()
    session.commit.assert_not_called()


def test_connect_rejects_different_repository_without_mutating_existing_record() -> None:
    candidate = make_candidate()
    existing_repository = GitHubRepository(
        candidate_id=candidate.id,
        repository_url="https://github.com/demo-user/existing-repository",
    )
    session = make_session(candidate, existing_repository)

    with pytest.raises(GitHubRepositoryConflictError):
        connect_github_repository(
            session, candidate.id, "https://github.com/demo-user/other-repository"
        )

    assert existing_repository.repository_url == "https://github.com/demo-user/existing-repository"
    session.add.assert_not_called()
    session.flush.assert_not_called()
    session.commit.assert_not_called()


def test_connect_rejects_missing_candidate_without_creating_repository() -> None:
    session = Mock()
    candidate_result = Mock()
    candidate_result.scalar_one_or_none.return_value = None
    session.execute.return_value = candidate_result

    with pytest.raises(CandidateProfileNotFoundError):
        connect_github_repository(session, uuid4(), "https://github.com/demo-user/demo-api")

    session.add.assert_not_called()
    session.flush.assert_not_called()
    session.commit.assert_not_called()


def test_connect_rejects_invalid_url_before_database_access() -> None:
    session = Mock()

    with pytest.raises(GitHubRepositoryUrlError):
        connect_github_repository(session, uuid4(), "http://github.com/demo-user/demo-api")

    session.execute.assert_not_called()
    session.add.assert_not_called()
    session.flush.assert_not_called()


def test_connect_propagates_failed_unique_flush_to_external_transaction_boundary() -> None:
    candidate = make_candidate()
    session = make_session(candidate, None)
    session.flush.side_effect = IntegrityError("insert", {}, Exception("unique violation"))

    with pytest.raises(IntegrityError):
        connect_github_repository(session, candidate.id, "https://github.com/demo-user/demo-api")

    session.add.assert_called_once()
    session.flush.assert_called_once()
    session.commit.assert_not_called()
    session.rollback.assert_not_called()

    session.rollback()

    session.rollback.assert_called_once()
    session.commit.assert_not_called()


def test_repository_model_retains_database_unique_constraint_per_candidate() -> None:
    assert any(
        isinstance(constraint, UniqueConstraint)
        and tuple(column.name for column in constraint.columns) == ("candidate_id",)
        for constraint in GitHubRepository.__table__.constraints
    )


def test_connect_does_not_create_evidence_or_use_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_network(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("Repository persistence service must not use network")

    monkeypatch.setattr(socket, "create_connection", fail_network)
    candidate = make_candidate()
    session = make_session(candidate, None)

    repository = connect_github_repository(
        session, candidate.id, "https://github.com/demo-user/demo-api"
    )

    added_models = [call.args[0] for call in session.add.call_args_list]
    assert repository in added_models
    assert not any(isinstance(model, EvidenceUnit) for model in added_models)
