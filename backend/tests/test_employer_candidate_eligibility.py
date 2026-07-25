"""Shared employer candidate eligibility policy tests."""

from collections.abc import Generator
from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import engine
from app.models.candidate_profile import CandidateProfile, OnboardingStatus
from app.models.user import User
from app.services.employer_candidate_eligibility import (
    EmployerCandidateUnavailableError,
    get_employer_eligible_candidate,
    list_employer_eligible_candidates,
    require_employer_eligible_candidate,
    trimmed_candidate_display_name,
)


@pytest.fixture
def postgres_session() -> Generator[Session, None, None]:
    try:
        connection = engine.connect()
    except SQLAlchemyError as error:
        pytest.skip(f"PostgreSQL is unavailable: {error}")
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


def _add_candidate(
    session: Session,
    *,
    display_name: str | None,
    role: str = "candidate",
    status: str = "active",
) -> CandidateProfile:
    user = User(
        id=uuid4(),
        email=f"eligible-{uuid4()}@example.com",
        password_hash="hash",
        role=role,
        status=status,
    )
    session.add(user)
    session.flush()
    profile = CandidateProfile(
        id=uuid4(),
        user_id=user.id,
        display_name=display_name,
        onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
    )
    session.add(profile)
    session.flush()
    return profile


def test_trimmed_display_name_helpers() -> None:
    named = CandidateProfile(
        id=uuid4(),
        user_id=uuid4(),
        display_name="  Ada  ",
        onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
    )
    blank = CandidateProfile(
        id=uuid4(),
        user_id=uuid4(),
        display_name="   ",
        onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
    )
    assert trimmed_candidate_display_name(named) == "Ada"
    assert trimmed_candidate_display_name(blank) is None
    assert trimmed_candidate_display_name(
        CandidateProfile(
            id=uuid4(),
            user_id=uuid4(),
            display_name=None,
            onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
        )
    ) is None


def test_active_named_candidate_is_eligible(postgres_session: Session) -> None:
    candidate = _add_candidate(postgres_session, display_name="  Nora Byte  ")
    postgres_session.commit()

    loaded = require_employer_eligible_candidate(postgres_session, candidate.id)
    listed_ids = {item.id for item in list_employer_eligible_candidates(postgres_session)}

    assert loaded.id == candidate.id
    assert trimmed_candidate_display_name(loaded) == "Nora Byte"
    assert candidate.id in listed_ids


@pytest.mark.parametrize("display_name", [None, "", "   "])
def test_empty_names_are_unavailable(
    postgres_session: Session, display_name: str | None
) -> None:
    candidate = _add_candidate(postgres_session, display_name=display_name)
    postgres_session.commit()

    assert get_employer_eligible_candidate(postgres_session, candidate.id) is None
    with pytest.raises(EmployerCandidateUnavailableError):
        require_employer_eligible_candidate(postgres_session, candidate.id)
    assert candidate.id not in {
        item.id for item in list_employer_eligible_candidates(postgres_session)
    }


def test_suspended_named_candidate_is_unavailable(postgres_session: Session) -> None:
    candidate = _add_candidate(
        postgres_session, display_name="Suspended Person", status="suspended"
    )
    postgres_session.commit()

    assert get_employer_eligible_candidate(postgres_session, candidate.id) is None
    with pytest.raises(EmployerCandidateUnavailableError):
        require_employer_eligible_candidate(postgres_session, candidate.id)


def test_employer_role_profile_anomaly_is_unavailable(postgres_session: Session) -> None:
    candidate = _add_candidate(
        postgres_session, display_name="Employer Profile", role="employer"
    )
    postgres_session.commit()

    assert get_employer_eligible_candidate(postgres_session, candidate.id) is None
    with pytest.raises(EmployerCandidateUnavailableError):
        require_employer_eligible_candidate(postgres_session, candidate.id)


def test_missing_candidate_is_unavailable(postgres_session: Session) -> None:
    assert get_employer_eligible_candidate(postgres_session, uuid4()) is None
    with pytest.raises(EmployerCandidateUnavailableError):
        require_employer_eligible_candidate(postgres_session, uuid4())
