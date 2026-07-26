"""API contract tests for candidate apply / withdraw."""

from collections.abc import Callable, Generator
from dataclasses import dataclass
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.dependencies import require_candidate
from app.db.session import engine, get_db
from app.main import app
from app.models.application import Application
from app.models.candidate_profile import CandidateProfile, OnboardingStatus
from app.models.employer_profile import EmployerProfile
from app.models.user import User
from app.models.vacancy import Vacancy
from app.services.candidate_vacancies import CandidateVacancyMatch
from app.services.matching import MatchResult, SkillGroupBreakdown


@dataclass(frozen=True)
class ApplicationApiContext:
    candidate_user: User
    candidate: CandidateProfile
    vacancy: Vacancy
    closed_vacancy: Vacancy
    new_session: Callable[[], Session]


def _match_item(vacancy: Vacancy, *, title: str | None = None) -> CandidateVacancyMatch:
    return CandidateVacancyMatch(
        vacancy=SimpleNamespace(
            id=vacancy.id,
            title=title or vacancy.title,
            description=vacancy.description,
            created_at=vacancy.created_at or datetime.now(UTC),
        ),
        company_name="Acme",
        required_skills=("Python",),
        preferred_skills=(),
        match=MatchResult(
            score=80,
            required=SkillGroupBreakdown(matched=("Python",), missing=()),
            preferred=SkillGroupBreakdown(matched=(), missing=()),
        ),
    )


@pytest.fixture
def application_client() -> Generator[tuple[TestClient, ApplicationApiContext], None, None]:
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
    candidate_user = User(
        id=uuid4(),
        email=f"apply-candidate-{uuid4()}@example.com",
        password_hash="hash",
        role="candidate",
        status="active",
    )
    employer_user = User(
        id=uuid4(),
        email=f"apply-employer-{uuid4()}@example.com",
        password_hash="hash",
        role="employer",
        status="active",
    )
    employer = EmployerProfile(
        id=uuid4(), user_id=employer_user.id, company_name="Apply Employer"
    )
    candidate = CandidateProfile(
        id=uuid4(),
        user_id=candidate_user.id,
        display_name="Apply Candidate",
        onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
    )
    vacancy = Vacancy(
        id=uuid4(),
        employer_id=employer.id,
        title="Backend Engineer",
        description="Build APIs",
        status="open",
    )
    closed_vacancy = Vacancy(
        id=uuid4(),
        employer_id=employer.id,
        title="Closed Role",
        description="Closed",
        status="closed",
    )
    setup.add_all(
        [candidate_user, employer_user, employer, candidate, vacancy, closed_vacancy]
    )
    setup.commit()
    setup.close()

    def new_session() -> Session:
        return Session(bind=connection, join_transaction_mode="create_savepoint")

    def request_session() -> Generator[Session, None, None]:
        session = new_session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = request_session
    app.dependency_overrides[require_candidate] = lambda: candidate_user
    context = ApplicationApiContext(
        candidate_user=candidate_user,
        candidate=candidate,
        vacancy=vacancy,
        closed_vacancy=closed_vacancy,
        new_session=new_session,
    )
    try:
        with TestClient(app) as client:
            yield client, context
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        connection.close()


def _application_path(vacancy_id: UUID) -> str:
    return f"/api/v1/candidate/vacancies/{vacancy_id}/application"


def test_apply_withdraw_and_reapply(
    application_client: tuple[TestClient, ApplicationApiContext],
) -> None:
    client, context = application_client

    created = client.post(_application_path(context.vacancy.id))
    assert created.status_code == 201
    body = created.json()
    assert body["vacancy_id"] == str(context.vacancy.id)
    assert body["candidate_id"] == str(context.candidate.id)
    assert body["status"] == "applied"
    application_id = body["id"]

    duplicate = client.post(_application_path(context.vacancy.id))
    assert duplicate.status_code == 201
    assert duplicate.json()["id"] == application_id
    assert duplicate.json()["status"] == "applied"

    withdrawn = client.patch(
        _application_path(context.vacancy.id),
        json={"status": "withdrawn"},
    )
    assert withdrawn.status_code == 200
    assert withdrawn.json()["id"] == application_id
    assert withdrawn.json()["status"] == "withdrawn"

    reapplied = client.post(_application_path(context.vacancy.id))
    assert reapplied.status_code == 201
    assert reapplied.json()["id"] == application_id
    assert reapplied.json()["status"] == "applied"

    session = context.new_session()
    try:
        from sqlalchemy import select

        rows = list(
            session.execute(
                select(Application).where(
                    Application.vacancy_id == context.vacancy.id,
                    Application.candidate_id == context.candidate.id,
                )
            )
            .scalars()
            .all()
        )
        assert len(rows) == 1
        assert rows[0].status == "applied"
    finally:
        session.close()


def test_apply_to_closed_vacancy_returns_404(
    application_client: tuple[TestClient, ApplicationApiContext],
) -> None:
    client, context = application_client
    response = client.post(_application_path(context.closed_vacancy.id))
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "VACANCY_NOT_FOUND"


def test_application_state_on_vacancy_list_and_detail(
    application_client: tuple[TestClient, ApplicationApiContext],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.api.v1 import candidate

    client, context = application_client
    item = _match_item(context.vacancy)
    monkeypatch.setattr(
        candidate, "list_candidate_vacancies", lambda *_args: [item]
    )
    monkeypatch.setattr(candidate, "get_candidate_vacancy", lambda *_args: item)
    monkeypatch.setattr(candidate, "vacancy_roadmap", lambda *_args: SimpleNamespace(items=[]))

    before_list = client.get("/api/v1/candidate/vacancies")
    assert before_list.status_code == 200
    assert before_list.json()[0]["application"] is None

    before_detail = client.get(f"/api/v1/candidate/vacancies/{context.vacancy.id}")
    assert before_detail.status_code == 200
    assert before_detail.json()["application"] is None

    applied = client.post(_application_path(context.vacancy.id))
    assert applied.status_code == 201

    after_list = client.get("/api/v1/candidate/vacancies")
    assert after_list.status_code == 200
    assert after_list.json()[0]["application"]["status"] == "applied"
    assert after_list.json()[0]["application"]["id"] == applied.json()["id"]

    after_detail = client.get(f"/api/v1/candidate/vacancies/{context.vacancy.id}")
    assert after_detail.status_code == 200
    assert after_detail.json()["application"]["status"] == "applied"


@pytest.fixture
def mocked_application_client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: Mock()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_mocked_list_includes_null_application_without_db_query(
    mocked_application_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import candidate

    user = User(
        id=uuid4(),
        email="candidate@example.com",
        password_hash="hash",
        role="candidate",
        status="active",
    )
    profile = CandidateProfile(
        id=uuid4(),
        user_id=user.id,
        display_name="Candidate",
        onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
    )
    vacancy_id = uuid4()
    item = CandidateVacancyMatch(
        vacancy=SimpleNamespace(
            id=vacancy_id,
            title="Role",
            description=None,
            created_at=datetime.now(UTC),
        ),
        company_name="Acme",
        required_skills=("Python",),
        preferred_skills=(),
        match=MatchResult(
            score=50,
            required=SkillGroupBreakdown(matched=(), missing=("Python",)),
            preferred=SkillGroupBreakdown(matched=(), missing=()),
        ),
    )
    app.dependency_overrides[require_candidate] = lambda: user
    monkeypatch.setattr(candidate, "get_candidate_profile", lambda *_args: profile)
    monkeypatch.setattr(candidate, "list_candidate_vacancies", lambda *_args: [item])
    monkeypatch.setattr(candidate, "map_applications_for_candidate", lambda *_args, **_kwargs: {})

    response = mocked_application_client.get("/api/v1/candidate/vacancies")
    assert response.status_code == 200
    assert response.json()[0]["application"] is None
