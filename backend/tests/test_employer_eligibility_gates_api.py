"""Cross-flow employer eligibility gates for match details and dependents."""

from __future__ import annotations

from collections.abc import Callable, Generator
from dataclasses import dataclass
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.dependencies import require_employer
from app.db.session import engine, get_db
from app.main import app
from app.models.candidate_profile import CandidateProfile, OnboardingStatus
from app.models.employer_profile import EmployerProfile
from app.models.user import User
from app.models.vacancy import Vacancy


@dataclass(frozen=True)
class EligibilityApiContext:
    employer_user: User
    vacancy: Vacancy
    eligible_id: UUID
    shell_id: UUID
    suspended_id: UUID
    new_session: Callable[[], Session]


@pytest.fixture
def eligibility_client() -> Generator[tuple[TestClient, EligibilityApiContext], None, None]:
    try:
        connection = engine.connect()
    except SQLAlchemyError as error:
        pytest.skip(f"PostgreSQL is unavailable: {error}")

    transaction = connection.begin()
    setup = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )
    employer_user = User(
        id=uuid4(),
        email=f"elig-employer-{uuid4()}@example.com",
        password_hash="hash",
        role="employer",
        status="active",
    )
    eligible_user = User(
        id=uuid4(),
        email=f"elig-candidate-{uuid4()}@example.com",
        password_hash="hash",
        role="candidate",
        status="active",
    )
    shell_user = User(
        id=uuid4(),
        email=f"elig-shell-{uuid4()}@example.com",
        password_hash="hash",
        role="candidate",
        status="active",
    )
    suspended_user = User(
        id=uuid4(),
        email=f"elig-suspended-{uuid4()}@example.com",
        password_hash="hash",
        role="candidate",
        status="suspended",
    )
    employer = EmployerProfile(
        id=uuid4(), user_id=employer_user.id, company_name="Eligibility Employer"
    )
    eligible = CandidateProfile(
        id=uuid4(),
        user_id=eligible_user.id,
        display_name="Eligible Candidate",
        onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
    )
    shell = CandidateProfile(
        id=uuid4(),
        user_id=shell_user.id,
        display_name=None,
        onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
    )
    suspended = CandidateProfile(
        id=uuid4(),
        user_id=suspended_user.id,
        display_name="Suspended Candidate",
        onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
    )
    vacancy = Vacancy(
        id=uuid4(), employer_id=employer.id, title="Backend Engineer", status="open"
    )
    setup.add_all(
        [
            employer_user,
            eligible_user,
            shell_user,
            suspended_user,
            employer,
            eligible,
            shell,
            suspended,
            vacancy,
        ]
    )
    setup.commit()
    setup.close()

    def new_session() -> Session:
        return Session(bind=connection, join_transaction_mode="create_savepoint")

    context = EligibilityApiContext(
        employer_user=employer_user,
        vacancy=vacancy,
        eligible_id=eligible.id,
        shell_id=shell.id,
        suspended_id=suspended.id,
        new_session=new_session,
    )

    def request_session() -> Generator[Session, None, None]:
        session = new_session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = request_session
    app.dependency_overrides[require_employer] = lambda: employer_user
    try:
        with TestClient(app) as client:
            yield client, context
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        connection.close()


def _match_path(candidate_id: UUID, vacancy_id: UUID, suffix: str = "") -> str:
    base = f"/api/v1/employer/matches/{candidate_id}{suffix}"
    return f"{base}?vacancy_id={vacancy_id}"


def test_match_details_rejects_shell_and_suspended(
    eligibility_client: tuple[TestClient, EligibilityApiContext],
) -> None:
    client, context = eligibility_client
    for candidate_id in (context.shell_id, context.suspended_id):
        response = client.get(_match_path(candidate_id, context.vacancy.id))
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "CANDIDATE_NOT_FOUND"


def test_match_details_allows_valid_named_zero_percent_candidate(
    eligibility_client: tuple[TestClient, EligibilityApiContext],
) -> None:
    client, context = eligibility_client
    response = client.get(_match_path(context.eligible_id, context.vacancy.id))
    assert response.status_code == 200
    body = response.json()
    assert body["candidate"]["id"] == str(context.eligible_id)
    assert body["candidate"]["name"] == "Eligible Candidate"
    assert "Unnamed" not in body["candidate"]["name"]
    assert body["match"]["score"] == 0


def test_ai_hiring_rejects_ineligible_before_provider(
    eligibility_client: tuple[TestClient, EligibilityApiContext],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, context = eligibility_client
    spy = MagicMock(side_effect=AssertionError("AI provider must not run"))
    monkeypatch.setattr("app.api.v1.employer.get_hiring_intelligence", spy)
    monkeypatch.setattr("app.api.v1.employer.build_hiring_context", spy)
    monkeypatch.setattr("app.api.v1.employer.build_passport", spy)

    for candidate_id in (context.shell_id, context.suspended_id):
        response = client.get(
            _match_path(candidate_id, context.vacancy.id, "/ai-hiring-intelligence")
        )
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "CANDIDATE_NOT_FOUND"
    spy.assert_not_called()


def test_interview_questions_rejects_ineligible_before_provider(
    eligibility_client: tuple[TestClient, EligibilityApiContext],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, context = eligibility_client
    spy = MagicMock(side_effect=AssertionError("Questions provider must not run"))
    monkeypatch.setattr("app.api.v1.employer.get_interview_questions", spy)
    monkeypatch.setattr("app.api.v1.employer.build_interview_questions_context", spy)

    for candidate_id in (context.shell_id, context.suspended_id):
        response = client.get(
            _match_path(candidate_id, context.vacancy.id, "/interview-questions")
        )
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "CANDIDATE_NOT_FOUND"
    spy.assert_not_called()


def test_match_explanation_rejects_ineligible_before_provider(
    eligibility_client: tuple[TestClient, EligibilityApiContext],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, context = eligibility_client
    spy = MagicMock(side_effect=AssertionError("Explanation provider must not run"))
    monkeypatch.setattr("app.api.v1.employer.explain_match", spy)
    monkeypatch.setattr("app.api.v1.employer.build_explanation_input", spy)
    monkeypatch.setattr("app.api.v1.employer.build_passport", spy)

    for candidate_id in (context.shell_id, context.suspended_id):
        response = client.post(_match_path(candidate_id, context.vacancy.id, "/explanation"))
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "CANDIDATE_NOT_FOUND"
    spy.assert_not_called()
