"""API contract tests for Interview Scorecard."""

from collections.abc import Callable, Generator
from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.dependencies import require_employer
from app.api.errors import api_error
from app.db.session import engine, get_db
from app.main import app
from app.models.application import Application
from app.models.candidate_profile import CandidateProfile, OnboardingStatus
from app.models.employer_candidate_shortlist import EmployerCandidateShortlist
from app.models.employer_interview_scorecard import EmployerInterviewScorecard
from app.models.employer_profile import EmployerProfile
from app.models.user import User
from app.models.vacancy import Vacancy
from app.services.employer_shortlist import save_candidate_to_shortlist


@dataclass(frozen=True)
class ScorecardApiContext:
    employer_user: User
    employer: EmployerProfile
    other_employer: EmployerProfile
    vacancy: Vacancy
    foreign_vacancy: Vacancy
    candidate_ids: tuple[UUID, UUID]
    new_session: Callable[[], Session]


RESPONSE_KEYS = {
    "id",
    "vacancy_id",
    "candidate_id",
    "technical_competency",
    "experience_relevance",
    "communication",
    "ownership",
    "interview_summary",
    "interview_notes",
    "recommendation",
    "created_at",
    "updated_at",
}


@pytest.fixture
def scorecard_client() -> Generator[tuple[TestClient, ScorecardApiContext], None, None]:
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
        email=f"scorecard-api-{uuid4()}@example.com",
        password_hash="hash",
        role="employer",
        status="active",
    )
    other_employer_user = User(
        id=uuid4(),
        email=f"scorecard-other-{uuid4()}@example.com",
        password_hash="hash",
        role="employer",
        status="active",
    )
    employer = EmployerProfile(
        id=uuid4(), user_id=employer_user.id, company_name="Scorecard Employer"
    )
    other_employer = EmployerProfile(
        id=uuid4(), user_id=other_employer_user.id, company_name="Other Employer"
    )
    vacancy = Vacancy(id=uuid4(), employer_id=employer.id, title="Backend Engineer", status="open")
    foreign_vacancy = Vacancy(
        id=uuid4(), employer_id=other_employer.id, title="Foreign Vacancy", status="open"
    )
    candidate_users = [
        User(
            id=uuid4(),
            email=f"scorecard-candidate-{uuid4()}@example.com",
            password_hash="hash",
            role="candidate",
            status="active",
        )
        for _ in range(2)
    ]
    candidates = [
        CandidateProfile(
            id=uuid4(),
            user_id=user.id,
            display_name=f"Candidate {index}",
            onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
        )
        for index, user in enumerate(candidate_users, start=1)
    ]
    applications = [
        Application(
            id=uuid4(),
            vacancy_id=vacancy.id,
            candidate_id=candidate.id,
            status="applied",
        )
        for candidate in candidates
    ]
    setup.add_all(
        [
            employer_user,
            other_employer_user,
            *candidate_users,
            employer,
            other_employer,
            vacancy,
            foreign_vacancy,
            *candidates,
            *applications,
        ]
    )
    setup.commit()
    setup.close()

    def new_session() -> Session:
        return Session(bind=connection, join_transaction_mode="create_savepoint")

    context = ScorecardApiContext(
        employer_user=employer_user,
        employer=employer,
        other_employer=other_employer,
        vacancy=vacancy,
        foreign_vacancy=foreign_vacancy,
        candidate_ids=(candidates[0].id, candidates[1].id),
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


def _path(vacancy_id: UUID, candidate_id: UUID) -> str:
    return f"/api/v1/employer/vacancies/{vacancy_id}/scorecards/{candidate_id}"


def _payload(**overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "technical_competency": 4,
        "experience_relevance": 3,
        "communication": 5,
        "ownership": 4,
        "interview_summary": "Solid technical depth.",
        "interview_notes": "Asked about distributed systems.",
        "recommendation": "yes",
    }
    body.update(overrides)
    return body


def test_get_before_create_returns_scorecard_not_found(
    scorecard_client: tuple[TestClient, ScorecardApiContext],
) -> None:
    client, context = scorecard_client
    response = client.get(_path(context.vacancy.id, context.candidate_ids[0]))
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SCORECARD_NOT_FOUND"


def test_put_create_get_and_replace(
    scorecard_client: tuple[TestClient, ScorecardApiContext],
) -> None:
    client, context = scorecard_client
    created = client.put(
        _path(context.vacancy.id, context.candidate_ids[0]),
        json=_payload(),
    )
    assert created.status_code == 200
    body = created.json()
    assert set(body.keys()) == RESPONSE_KEYS
    assert "employer_id" not in body
    assert body["vacancy_id"] == str(context.vacancy.id)
    assert body["candidate_id"] == str(context.candidate_ids[0])
    assert body["technical_competency"] == 4
    assert body["recommendation"] == "yes"

    fetched = client.get(_path(context.vacancy.id, context.candidate_ids[0]))
    assert fetched.status_code == 200
    assert fetched.json()["id"] == body["id"]
    assert fetched.json()["interview_summary"] == "Solid technical depth."

    replaced = client.put(
        _path(context.vacancy.id, context.candidate_ids[0]),
        json=_payload(
            technical_competency=2,
            experience_relevance=2,
            communication=2,
            ownership=2,
            interview_summary=None,
            interview_notes="",
            recommendation="no",
        ),
    )
    assert replaced.status_code == 200
    assert replaced.json()["id"] == body["id"]
    assert replaced.json()["technical_competency"] == 2
    assert replaced.json()["recommendation"] == "no"
    assert replaced.json()["interview_summary"] is None
    assert replaced.json()["interview_notes"] is None
    assert replaced.json()["created_at"] == body["created_at"]


def test_missing_and_foreign_vacancy_return_404(
    scorecard_client: tuple[TestClient, ScorecardApiContext],
) -> None:
    client, context = scorecard_client
    missing = client.put(_path(uuid4(), context.candidate_ids[0]), json=_payload())
    assert missing.status_code == 404
    foreign = client.put(
        _path(context.foreign_vacancy.id, context.candidate_ids[0]),
        json=_payload(),
    )
    assert foreign.status_code == 404
    foreign_get = client.get(_path(context.foreign_vacancy.id, context.candidate_ids[0]))
    assert foreign_get.status_code == 404


def test_missing_candidate_returns_404(
    scorecard_client: tuple[TestClient, ScorecardApiContext],
) -> None:
    client, context = scorecard_client
    missing_id = uuid4()
    put_response = client.put(_path(context.vacancy.id, missing_id), json=_payload())
    assert put_response.status_code == 404
    assert put_response.json()["error"]["code"] == "CANDIDATE_NOT_FOUND"
    get_response = client.get(_path(context.vacancy.id, missing_id))
    assert get_response.status_code == 404
    assert get_response.json()["error"]["code"] == "CANDIDATE_NOT_FOUND"


def test_candidate_role_and_unauthenticated_rejected(
    scorecard_client: tuple[TestClient, ScorecardApiContext],
) -> None:
    client, context = scorecard_client
    path = _path(context.vacancy.id, context.candidate_ids[0])

    app.dependency_overrides[require_employer] = lambda: (_ for _ in ()).throw(
        api_error(403, "FORBIDDEN", "Employer role required")
    )
    forbidden = client.put(path, json=_payload())
    assert forbidden.status_code == 403

    app.dependency_overrides.pop(require_employer, None)
    unauthenticated = client.put(path, json=_payload())
    assert unauthenticated.status_code == 401

    app.dependency_overrides[require_employer] = lambda: context.employer_user


def test_validation_errors_return_422(
    scorecard_client: tuple[TestClient, ScorecardApiContext],
) -> None:
    client, context = scorecard_client
    path = _path(context.vacancy.id, context.candidate_ids[0])
    invalid_score = client.put(path, json=_payload(technical_competency=0))
    assert invalid_score.status_code == 422
    invalid_rec = client.put(path, json=_payload(recommendation="hire"))
    assert invalid_rec.status_code == 422
    unknown = client.put(path, json=_payload(overall_score=3))
    assert unknown.status_code == 422


def test_no_pipeline_or_shortlist_side_effects(
    scorecard_client: tuple[TestClient, ScorecardApiContext],
) -> None:
    client, context = scorecard_client
    session = context.new_session()
    try:
        entry = save_candidate_to_shortlist(
            session,
            vacancy=context.vacancy,
            candidate_id=context.candidate_ids[0],
        )
        entry.stage = "interview"
        entry.note = "Private shortlist note"
        session.commit()
        shortlist_id = entry.id
    finally:
        session.close()

    response = client.put(
        _path(context.vacancy.id, context.candidate_ids[0]),
        json=_payload(recommendation="strong_yes"),
    )
    assert response.status_code == 200

    verify = context.new_session()
    try:
        shortlist = verify.get(EmployerCandidateShortlist, shortlist_id)
        assert shortlist is not None
        assert shortlist.stage == "interview"
        assert shortlist.note == "Private shortlist note"
        scorecards = list(
            verify.execute(
                select(EmployerInterviewScorecard).where(
                    EmployerInterviewScorecard.vacancy_id == context.vacancy.id
                )
            )
            .scalars()
            .all()
        )
        assert len(scorecards) == 1
    finally:
        verify.close()


def test_put_does_not_require_shortlist(
    scorecard_client: tuple[TestClient, ScorecardApiContext],
) -> None:
    client, context = scorecard_client
    response = client.put(
        _path(context.vacancy.id, context.candidate_ids[1]),
        json=_payload(),
    )
    assert response.status_code == 200
    session = context.new_session()
    try:
        shortlist = session.execute(
            select(EmployerCandidateShortlist).where(
                EmployerCandidateShortlist.candidate_id == context.candidate_ids[1],
                EmployerCandidateShortlist.vacancy_id == context.vacancy.id,
            )
        ).scalar_one_or_none()
        assert shortlist is None
    finally:
        session.close()


def test_scorecard_rejects_shell_and_suspended_candidates(
    scorecard_client: tuple[TestClient, ScorecardApiContext],
) -> None:
    client, context = scorecard_client
    session = context.new_session()
    try:
        shell_user = User(
            id=uuid4(),
            email=f"scorecard-shell-{uuid4()}@example.com",
            password_hash="hash",
            role="candidate",
            status="active",
        )
        suspended_user = User(
            id=uuid4(),
            email=f"scorecard-suspended-{uuid4()}@example.com",
            password_hash="hash",
            role="candidate",
            status="suspended",
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
            display_name="Suspended Scorecard",
            onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
        )
        session.add_all([shell_user, suspended_user, shell, suspended])
        session.commit()
        shell_id = shell.id
        suspended_id = suspended.id
    finally:
        session.close()

    for candidate_id in (shell_id, suspended_id):
        put_response = client.put(_path(context.vacancy.id, candidate_id), json=_payload())
        get_response = client.get(_path(context.vacancy.id, candidate_id))
        assert put_response.status_code == 404
        assert put_response.json()["error"]["code"] == "CANDIDATE_NOT_FOUND"
        assert get_response.status_code == 404
        assert get_response.json()["error"]["code"] == "CANDIDATE_NOT_FOUND"
