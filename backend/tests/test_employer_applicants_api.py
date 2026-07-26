"""API contract tests for employer applicants and contact disclosure."""

from collections.abc import Callable, Generator
from dataclasses import dataclass
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


@dataclass(frozen=True)
class ApplicantsApiContext:
    employer_user: User
    employer: EmployerProfile
    other_employer: EmployerProfile
    vacancy: Vacancy
    foreign_vacancy: Vacancy
    applied_candidate_id: UUID
    withdrawn_candidate_id: UUID
    never_applied_candidate_id: UUID
    new_session: Callable[[], Session]


@pytest.fixture
def applicants_client() -> Generator[tuple[TestClient, ApplicantsApiContext], None, None]:
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
        email=f"applicants-employer-{uuid4()}@example.com",
        password_hash="hash",
        role="employer",
        status="active",
    )
    other_employer_user = User(
        id=uuid4(),
        email=f"applicants-other-{uuid4()}@example.com",
        password_hash="hash",
        role="employer",
        status="active",
    )
    employer = EmployerProfile(
        id=uuid4(), user_id=employer_user.id, company_name="Applicants Employer"
    )
    other_employer = EmployerProfile(
        id=uuid4(), user_id=other_employer_user.id, company_name="Other Employer"
    )
    vacancy = Vacancy(
        id=uuid4(), employer_id=employer.id, title="Backend Engineer", status="open"
    )
    foreign_vacancy = Vacancy(
        id=uuid4(), employer_id=other_employer.id, title="Foreign Role", status="open"
    )
    candidate_users = [
        User(
            id=uuid4(),
            email=f"applicants-candidate-{uuid4()}@example.com",
            password_hash="hash",
            role="candidate",
            status="active",
        )
        for _ in range(3)
    ]
    applied = CandidateProfile(
        id=uuid4(),
        user_id=candidate_users[0].id,
        display_name="Applied Candidate",
        phone="+77001112233",
        telegram="@applied",
        linkedin_url="https://linkedin.com/in/applied",
        portfolio_url="https://portfolio.example/applied",
        location="Almaty",
        onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
    )
    withdrawn = CandidateProfile(
        id=uuid4(),
        user_id=candidate_users[1].id,
        display_name="Withdrawn Candidate",
        phone="+77004445566",
        telegram="@withdrawn",
        onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
    )
    never_applied = CandidateProfile(
        id=uuid4(),
        user_id=candidate_users[2].id,
        display_name="Recommended Only",
        phone="+77007778899",
        telegram="@recommended",
        onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
    )
    skill = Skill(
        id=uuid4(),
        canonical_name=f"Python-{uuid4().hex[:8]}",
        normalized_name=f"python-{uuid4().hex[:8]}",
        category="backend",
        ontology_version="test",
        deprecated=False,
    )
    requirement = VacancySkillRequirement(
        id=uuid4(),
        vacancy_id=vacancy.id,
        skill_id=skill.id,
        requirement_type="required",
    )
    applications = [
        Application(
            id=uuid4(),
            vacancy_id=vacancy.id,
            candidate_id=applied.id,
            status="applied",
        ),
        Application(
            id=uuid4(),
            vacancy_id=vacancy.id,
            candidate_id=withdrawn.id,
            status="withdrawn",
        ),
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
            applied,
            withdrawn,
            never_applied,
            skill,
        ]
    )
    setup.flush()
    setup.add_all([requirement, *applications])
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
    app.dependency_overrides[require_employer] = lambda: employer_user
    context = ApplicantsApiContext(
        employer_user=employer_user,
        employer=employer,
        other_employer=other_employer,
        vacancy=vacancy,
        foreign_vacancy=foreign_vacancy,
        applied_candidate_id=applied.id,
        withdrawn_candidate_id=withdrawn.id,
        never_applied_candidate_id=never_applied.id,
        new_session=new_session,
    )
    try:
        with TestClient(app) as client:
            yield client, context
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        connection.close()


def _applicants_path(vacancy_id: UUID) -> str:
    return f"/api/v1/employer/vacancies/{vacancy_id}/applicants"


def _contact_path(vacancy_id: UUID, candidate_id: UUID) -> str:
    return f"/api/v1/employer/vacancies/{vacancy_id}/applicants/{candidate_id}/contact"


def test_empty_applicants_list(
    applicants_client: tuple[TestClient, ApplicantsApiContext],
) -> None:
    from sqlalchemy import delete

    client, context = applicants_client
    session = context.new_session()
    try:
        session.execute(
            delete(Application).where(Application.vacancy_id == context.vacancy.id)
        )
        session.commit()
    finally:
        session.close()

    response = client.get(_applicants_path(context.vacancy.id))
    assert response.status_code == 200
    assert response.json() == {"applicants": []}


def test_list_only_active_applicants(
    applicants_client: tuple[TestClient, ApplicantsApiContext],
) -> None:
    client, context = applicants_client
    response = client.get(_applicants_path(context.vacancy.id))
    assert response.status_code == 200
    body = response.json()
    assert len(body["applicants"]) == 1
    applicant = body["applicants"][0]
    assert applicant["candidate_id"] == str(context.applied_candidate_id)
    assert applicant["candidate_name"] == "Applied Candidate"
    assert applicant["status"] == "applied"
    assert set(applicant) >= {
        "application_id",
        "candidate_id",
        "candidate_name",
        "status",
        "applied_at",
        "score",
        "required",
        "preferred",
    }


def test_contact_visible_for_active_applicant(
    applicants_client: tuple[TestClient, ApplicantsApiContext],
) -> None:
    client, context = applicants_client
    response = client.get(
        _contact_path(context.vacancy.id, context.applied_candidate_id)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["phone"] == "+77001112233"
    assert body["telegram"] == "@applied"
    assert body["linkedin_url"] == "https://linkedin.com/in/applied"
    assert body["portfolio_url"] == "https://portfolio.example/applied"
    assert body["location"] == "Almaty"
    assert "@" in body["email"]


def test_contact_404_for_unrelated_withdrawn_and_foreign(
    applicants_client: tuple[TestClient, ApplicantsApiContext],
) -> None:
    client, context = applicants_client

    never_applied = client.get(
        _contact_path(context.vacancy.id, context.never_applied_candidate_id)
    )
    assert never_applied.status_code == 404
    assert never_applied.json()["error"]["code"] == "APPLICANT_NOT_FOUND"

    withdrawn = client.get(
        _contact_path(context.vacancy.id, context.withdrawn_candidate_id)
    )
    assert withdrawn.status_code == 404
    assert withdrawn.json()["error"]["code"] == "APPLICANT_NOT_FOUND"

    foreign = client.get(
        _contact_path(context.foreign_vacancy.id, context.applied_candidate_id)
    )
    assert foreign.status_code == 404


def test_recommendations_still_include_non_applicants(
    applicants_client: tuple[TestClient, ApplicantsApiContext],
) -> None:
    client, context = applicants_client
    response = client.get(f"/api/v1/employer/vacancies/{context.vacancy.id}/matches")
    assert response.status_code == 200
    matches = response.json()["matches"]
    candidate_ids = {item["candidate_id"] for item in matches}
    assert str(context.never_applied_candidate_id) in candidate_ids
    assert str(context.applied_candidate_id) in candidate_ids
    assert str(context.withdrawn_candidate_id) in candidate_ids
