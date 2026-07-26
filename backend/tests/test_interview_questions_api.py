"""API contract tests for AI Interview Questions."""

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
from app.models.application import Application
from app.models.candidate_profile import CandidateProfile, OnboardingStatus
from app.models.employer_profile import EmployerProfile
from app.models.skill import Skill
from app.models.user import User
from app.models.vacancy import Vacancy
from app.models.vacancy_skill_requirement import VacancySkillRequirement
from app.services.interview_questions import clear_interview_questions_cache


@dataclass(frozen=True)
class InterviewQuestionsApiContext:
    employer_user: User
    employer: EmployerProfile
    vacancy: Vacancy
    foreign_vacancy: Vacancy
    candidate_id: UUID
    new_session: Callable[[], Session]


RESPONSE_KEYS = {"questions"}
QUESTION_KEYS = {
    "category",
    "question",
    "reason",
    "target_skill",
    "evidence_basis",
}


@pytest.fixture
def interview_questions_client() -> (
    Generator[tuple[TestClient, InterviewQuestionsApiContext], None, None]
):
    clear_interview_questions_cache()
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
        email=f"iq-employer-{uuid4()}@example.com",
        password_hash="hash",
        role="employer",
        status="active",
    )
    other_employer_user = User(
        id=uuid4(),
        email=f"iq-other-{uuid4()}@example.com",
        password_hash="hash",
        role="employer",
        status="active",
    )
    candidate_user = User(
        id=uuid4(),
        email=f"iq-candidate-{uuid4()}@example.com",
        password_hash="hash",
        role="candidate",
        status="active",
    )
    employer = EmployerProfile(id=uuid4(), user_id=employer_user.id, company_name="IQ Employer")
    other_employer = EmployerProfile(
        id=uuid4(), user_id=other_employer_user.id, company_name="Other Employer"
    )
    candidate = CandidateProfile(
        id=uuid4(),
        user_id=candidate_user.id,
        display_name="Alex Morgan",
        target_role="Backend Engineer",
        onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
    )
    vacancy = Vacancy(id=uuid4(), employer_id=employer.id, title="Backend Engineer", status="open")
    foreign_vacancy = Vacancy(
        id=uuid4(), employer_id=other_employer.id, title="Foreign Vacancy", status="open"
    )
    skill = Skill(
        id=uuid4(),
        canonical_name=f"Python-{uuid4().hex[:8]}",
        normalized_name=f"python-{uuid4().hex[:8]}",
        category="language",
        ontology_version="test",
    )
    requirement = VacancySkillRequirement(
        id=uuid4(),
        vacancy_id=vacancy.id,
        skill_id=skill.id,
        requirement_type="required",
    )
    application = Application(
        id=uuid4(),
        vacancy_id=vacancy.id,
        candidate_id=candidate.id,
        status="applied",
    )
    setup.add_all(
        [
            employer_user,
            other_employer_user,
            candidate_user,
            employer,
            other_employer,
            candidate,
            vacancy,
            foreign_vacancy,
            skill,
            requirement,
            application,
        ]
    )
    setup.commit()
    setup.close()

    def new_session() -> Session:
        return Session(bind=connection, join_transaction_mode="create_savepoint")

    context = InterviewQuestionsApiContext(
        employer_user=employer_user,
        employer=employer,
        vacancy=vacancy,
        foreign_vacancy=foreign_vacancy,
        candidate_id=candidate.id,
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
        clear_interview_questions_cache()
        transaction.rollback()
        connection.close()


def _path(candidate_id: UUID, vacancy_id: UUID, *, refresh: bool | None = None) -> str:
    query = f"vacancy_id={vacancy_id}"
    if refresh is not None:
        query += f"&refresh={'true' if refresh else 'false'}"
    return f"/api/v1/employer/matches/{candidate_id}/interview-questions?{query}"


def test_get_interview_questions_success(
    interview_questions_client: tuple[TestClient, InterviewQuestionsApiContext],
) -> None:
    client, context = interview_questions_client
    response = client.get(_path(context.candidate_id, context.vacancy.id))
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == RESPONSE_KEYS
    assert 1 <= len(body["questions"]) <= 8
    assert set(body["questions"][0].keys()) == QUESTION_KEYS
    assert "verdict" not in body
    assert "recommendation" not in body


def test_missing_candidate_returns_404(
    interview_questions_client: tuple[TestClient, InterviewQuestionsApiContext],
) -> None:
    client, context = interview_questions_client
    response = client.get(_path(uuid4(), context.vacancy.id))
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "APPLICANT_NOT_FOUND"


def test_foreign_vacancy_hidden(
    interview_questions_client: tuple[TestClient, InterviewQuestionsApiContext],
) -> None:
    client, context = interview_questions_client
    response = client.get(_path(context.candidate_id, context.foreign_vacancy.id))
    assert response.status_code == 404


def test_foreign_vacancy_does_not_call_provider(
    interview_questions_client: tuple[TestClient, InterviewQuestionsApiContext],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, context = interview_questions_client
    spy = MagicMock(side_effect=AssertionError("provider path must not run"))
    monkeypatch.setattr("app.api.v1.employer.get_interview_questions", spy)
    monkeypatch.setattr("app.api.v1.employer.build_interview_questions_context", spy)
    response = client.get(_path(context.candidate_id, context.foreign_vacancy.id))
    assert response.status_code == 404
    spy.assert_not_called()


def test_missing_candidate_does_not_call_provider(
    interview_questions_client: tuple[TestClient, InterviewQuestionsApiContext],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, context = interview_questions_client
    spy = MagicMock(side_effect=AssertionError("provider path must not run"))
    monkeypatch.setattr("app.api.v1.employer.get_interview_questions", spy)
    monkeypatch.setattr("app.api.v1.employer.build_interview_questions_context", spy)
    response = client.get(_path(uuid4(), context.vacancy.id))
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "APPLICANT_NOT_FOUND"
    spy.assert_not_called()


def test_missing_vacancy_id_does_not_call_provider(
    interview_questions_client: tuple[TestClient, InterviewQuestionsApiContext],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, context = interview_questions_client
    spy = MagicMock(side_effect=AssertionError("provider path must not run"))
    monkeypatch.setattr("app.api.v1.employer.get_interview_questions", spy)
    response = client.get(f"/api/v1/employer/matches/{context.candidate_id}/interview-questions")
    assert response.status_code == 422
    spy.assert_not_called()


def test_provider_failure_returns_503(
    interview_questions_client: tuple[TestClient, InterviewQuestionsApiContext],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, context = interview_questions_client

    def _boom(*_args: object, **_kwargs: object) -> object:
        from app.services.interview_questions import InterviewQuestionsUnavailableError

        raise InterviewQuestionsUnavailableError("boom")

    monkeypatch.setattr(
        "app.api.v1.employer.get_interview_questions",
        _boom,
    )
    response = client.get(_path(context.candidate_id, context.vacancy.id))
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "INTERVIEW_QUESTIONS_UNAVAILABLE"
    assert "boom" not in response.json()["error"]["message"].lower()


def test_refresh_query_accepted(
    interview_questions_client: tuple[TestClient, InterviewQuestionsApiContext],
) -> None:
    client, context = interview_questions_client
    first = client.get(_path(context.candidate_id, context.vacancy.id, refresh=False))
    second = client.get(_path(context.candidate_id, context.vacancy.id, refresh=True))
    assert first.status_code == 200
    assert second.status_code == 200
    assert set(second.json().keys()) == RESPONSE_KEYS


def test_no_post_put_patch_delete_routes(
    interview_questions_client: tuple[TestClient, InterviewQuestionsApiContext],
) -> None:
    client, context = interview_questions_client
    path = _path(context.candidate_id, context.vacancy.id)
    assert client.post(path).status_code == 405
    assert client.put(path).status_code == 405
    assert client.patch(path).status_code == 405
    assert client.delete(path).status_code == 405
