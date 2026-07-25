"""DB-backed tests for company update and vacancy deletion."""

from collections.abc import Callable, Generator
from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.dependencies import require_employer
from app.db.session import engine, get_db
from app.main import app
from app.models.candidate_profile import CandidateProfile, OnboardingStatus
from app.models.employer_candidate_shortlist import EmployerCandidateShortlist
from app.models.employer_interview_scorecard import EmployerInterviewScorecard
from app.models.employer_profile import EmployerProfile
from app.models.skill import Skill
from app.models.user import User
from app.models.vacancy import Vacancy
from app.models.vacancy_skill_requirement import VacancySkillRequirement


@dataclass(frozen=True)
class CompanyVacancyContext:
    employer_user: User
    other_employer_user: User
    orphan_employer_user: User
    employer: EmployerProfile
    other_employer: EmployerProfile
    vacancy: Vacancy
    second_vacancy: Vacancy
    foreign_vacancy: Vacancy
    candidate_id: UUID
    skill_id: UUID
    new_session: Callable[[], Session]


@pytest.fixture
def company_vacancy_client() -> Generator[tuple[TestClient, CompanyVacancyContext], None, None]:
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
        email=f"company-employer-{uuid4()}@example.com",
        password_hash="hash",
        role="employer",
        status="active",
    )
    other_employer_user = User(
        id=uuid4(),
        email=f"company-other-{uuid4()}@example.com",
        password_hash="hash",
        role="employer",
        status="active",
    )
    orphan_employer_user = User(
        id=uuid4(),
        email=f"company-orphan-{uuid4()}@example.com",
        password_hash="hash",
        role="employer",
        status="active",
    )
    employer = EmployerProfile(
        id=uuid4(),
        user_id=employer_user.id,
        company_name="Owned Company",
        website="https://owned.example",
        description="Original description",
    )
    other_employer = EmployerProfile(
        id=uuid4(),
        user_id=other_employer_user.id,
        company_name="Other Company",
        website="https://other.example",
        description="Other description",
    )
    vacancy = Vacancy(
        id=uuid4(), employer_id=employer.id, title="Owned Vacancy", status="open"
    )
    second_vacancy = Vacancy(
        id=uuid4(), employer_id=employer.id, title="Second Vacancy", status="open"
    )
    foreign_vacancy = Vacancy(
        id=uuid4(), employer_id=other_employer.id, title="Foreign Vacancy", status="open"
    )
    candidate_user = User(
        id=uuid4(),
        email=f"company-candidate-{uuid4()}@example.com",
        password_hash="hash",
        role="candidate",
        status="active",
    )
    candidate = CandidateProfile(
        id=uuid4(),
        user_id=candidate_user.id,
        display_name="Delete Candidate",
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
    shortlist = EmployerCandidateShortlist(
        id=uuid4(),
        employer_id=employer.id,
        vacancy_id=vacancy.id,
        candidate_id=candidate.id,
        stage="shortlisted",
        note="Keep for interview",
    )
    scorecard = EmployerInterviewScorecard(
        id=uuid4(),
        employer_id=employer.id,
        vacancy_id=vacancy.id,
        candidate_id=candidate.id,
        technical_competency=4,
        experience_relevance=4,
        communication=3,
        ownership=4,
        interview_summary="Solid",
        interview_notes=None,
        recommendation="yes",
    )
    foreign_requirement = VacancySkillRequirement(
        id=uuid4(),
        vacancy_id=foreign_vacancy.id,
        skill_id=skill.id,
        requirement_type="preferred",
    )
    second_requirement = VacancySkillRequirement(
        id=uuid4(),
        vacancy_id=second_vacancy.id,
        skill_id=skill.id,
        requirement_type="required",
    )

    setup.add_all(
        [
            employer_user,
            other_employer_user,
            orphan_employer_user,
            candidate_user,
            employer,
            other_employer,
            vacancy,
            second_vacancy,
            foreign_vacancy,
            candidate,
            skill,
        ]
    )
    setup.flush()
    setup.add_all(
        [
            requirement,
            shortlist,
            scorecard,
            foreign_requirement,
            second_requirement,
        ]
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
    app.dependency_overrides[require_employer] = lambda: employer_user

    context = CompanyVacancyContext(
        employer_user=employer_user,
        other_employer_user=other_employer_user,
        orphan_employer_user=orphan_employer_user,
        employer=employer,
        other_employer=other_employer,
        vacancy=vacancy,
        second_vacancy=second_vacancy,
        foreign_vacancy=foreign_vacancy,
        candidate_id=candidate.id,
        skill_id=skill.id,
        new_session=new_session,
    )

    with TestClient(app) as test_client:
        yield test_client, context

    app.dependency_overrides.clear()
    transaction.rollback()
    connection.close()


def test_owner_updates_company(
    company_vacancy_client: tuple[TestClient, CompanyVacancyContext],
) -> None:
    client, ctx = company_vacancy_client

    response = client.patch(
        "/api/v1/employer/company",
        json={
            "company_name": "Renamed Company",
            "website": "https://renamed.example",
            "description": "Updated description",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["company_name"] == "Renamed Company"
    assert body["website"] in {"https://renamed.example", "https://renamed.example/"}
    assert body["description"] == "Updated description"

    session = ctx.new_session()
    try:
        company = session.get(EmployerProfile, ctx.employer.id)
        assert company is not None
        assert company.company_name == "Renamed Company"
        assert company.website in {"https://renamed.example", "https://renamed.example/"}
        assert company.description == "Updated description"
        other = session.get(EmployerProfile, ctx.other_employer.id)
        assert other is not None
        assert other.company_name == "Other Company"
    finally:
        session.close()


def test_update_company_without_profile_returns_404(
    company_vacancy_client: tuple[TestClient, CompanyVacancyContext],
) -> None:
    client, ctx = company_vacancy_client
    app.dependency_overrides[require_employer] = lambda: ctx.orphan_employer_user

    response = client.patch(
        "/api/v1/employer/company",
        json={"company_name": "Should Fail"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "EMPLOYER_COMPANY_NOT_FOUND"


def test_another_employer_cannot_mutate_owned_company_fields(
    company_vacancy_client: tuple[TestClient, CompanyVacancyContext],
) -> None:
    """Company resource is user-scoped; another employer updates only their own row."""
    client, ctx = company_vacancy_client
    app.dependency_overrides[require_employer] = lambda: ctx.other_employer_user

    response = client.patch(
        "/api/v1/employer/company",
        json={"company_name": "Hijacked"},
    )
    assert response.status_code == 200
    assert response.json()["company_name"] == "Hijacked"
    assert response.json()["id"] == str(ctx.other_employer.id)

    session = ctx.new_session()
    try:
        owned = session.get(EmployerProfile, ctx.employer.id)
        assert owned is not None
        assert owned.company_name == "Owned Company"
    finally:
        session.close()


def test_partial_company_update_keeps_other_fields(
    company_vacancy_client: tuple[TestClient, CompanyVacancyContext],
) -> None:
    client, ctx = company_vacancy_client

    response = client.patch(
        "/api/v1/employer/company",
        json={"description": "Partial only"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["company_name"] == "Owned Company"
    assert body["website"] == "https://owned.example"
    assert body["description"] == "Partial only"


@pytest.mark.parametrize("company_name", ["", "   ", None, "x" * 161])
def test_invalid_company_name_does_not_change_profile(
    company_vacancy_client: tuple[TestClient, CompanyVacancyContext],
    company_name: str | None,
) -> None:
    client, ctx = company_vacancy_client

    response = client.patch(
        "/api/v1/employer/company",
        json={"company_name": company_name, "description": "Must not be saved"},
    )
    assert response.status_code == 422

    session = ctx.new_session()
    try:
        company = session.get(EmployerProfile, ctx.employer.id)
        assert company is not None
        assert company.company_name == "Owned Company"
        assert company.website == "https://owned.example"
        assert company.description == "Original description"
    finally:
        session.close()


def test_company_name_is_trimmed_by_existing_schema_convention(
    company_vacancy_client: tuple[TestClient, CompanyVacancyContext],
) -> None:
    client, ctx = company_vacancy_client

    response = client.patch(
        "/api/v1/employer/company",
        json={"company_name": "  Trimmed Company  "},
    )
    assert response.status_code == 200
    assert response.json()["company_name"] == "Trimmed Company"

    session = ctx.new_session()
    try:
        company = session.get(EmployerProfile, ctx.employer.id)
        assert company is not None
        assert company.company_name == "Trimmed Company"
    finally:
        session.close()


def test_explicit_null_clears_nullable_company_fields(
    company_vacancy_client: tuple[TestClient, CompanyVacancyContext],
) -> None:
    client, ctx = company_vacancy_client

    response = client.patch(
        "/api/v1/employer/company",
        json={"website": None, "description": None},
    )
    assert response.status_code == 200
    assert response.json()["company_name"] == "Owned Company"
    assert response.json()["website"] is None
    assert response.json()["description"] is None

    session = ctx.new_session()
    try:
        company = session.get(EmployerProfile, ctx.employer.id)
        assert company is not None
        assert company.company_name == "Owned Company"
        assert company.website is None
        assert company.description is None
    finally:
        session.close()


def test_empty_website_is_invalid_and_empty_description_is_preserved(
    company_vacancy_client: tuple[TestClient, CompanyVacancyContext],
) -> None:
    client, ctx = company_vacancy_client

    invalid_website = client.patch(
        "/api/v1/employer/company",
        json={"website": ""},
    )
    assert invalid_website.status_code == 422

    empty_description = client.patch(
        "/api/v1/employer/company",
        json={"description": ""},
    )
    assert empty_description.status_code == 200
    assert empty_description.json()["description"] == ""

    session = ctx.new_session()
    try:
        company = session.get(EmployerProfile, ctx.employer.id)
        assert company is not None
        assert company.website == "https://owned.example"
        assert company.description == ""
    finally:
        session.close()


def test_owner_can_delete_vacancy_and_related_rows(
    company_vacancy_client: tuple[TestClient, CompanyVacancyContext],
) -> None:
    client, ctx = company_vacancy_client

    response = client.delete(f"/api/v1/employer/vacancies/{ctx.vacancy.id}")
    assert response.status_code == 204
    assert response.content == b""

    session = ctx.new_session()
    try:
        assert session.get(Vacancy, ctx.vacancy.id) is None
        assert (
            session.scalar(
                select(func.count())
                .select_from(VacancySkillRequirement)
                .where(VacancySkillRequirement.vacancy_id == ctx.vacancy.id)
            )
            == 0
        )
        assert (
            session.scalar(
                select(func.count())
                .select_from(EmployerCandidateShortlist)
                .where(EmployerCandidateShortlist.vacancy_id == ctx.vacancy.id)
            )
            == 0
        )
        assert (
            session.scalar(
                select(func.count())
                .select_from(EmployerInterviewScorecard)
                .where(EmployerInterviewScorecard.vacancy_id == ctx.vacancy.id)
            )
            == 0
        )
        assert session.get(Vacancy, ctx.second_vacancy.id) is not None
        assert session.get(Vacancy, ctx.foreign_vacancy.id) is not None
        assert (
            session.scalar(
                select(func.count())
                .select_from(VacancySkillRequirement)
                .where(VacancySkillRequirement.vacancy_id == ctx.second_vacancy.id)
            )
            == 1
        )
        assert (
            session.scalar(
                select(func.count())
                .select_from(VacancySkillRequirement)
                .where(VacancySkillRequirement.vacancy_id == ctx.foreign_vacancy.id)
            )
            == 1
        )
        assert session.get(CandidateProfile, ctx.candidate_id) is not None
        assert session.get(Skill, ctx.skill_id) is not None
        assert session.get(User, ctx.employer_user.id) is not None
    finally:
        session.close()


def test_delete_vacancy_rolls_back_all_child_deletes_on_failure(
    company_vacancy_client: tuple[TestClient, CompanyVacancyContext],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, ctx = company_vacancy_client
    original_delete = Session.delete

    def fail_before_vacancy_delete(session: Session, instance: object) -> None:
        if isinstance(instance, Vacancy) and instance.id == ctx.vacancy.id:
            raise SQLAlchemyError("forced vacancy delete failure")
        original_delete(session, instance)

    monkeypatch.setattr(Session, "delete", fail_before_vacancy_delete)

    response = client.delete(f"/api/v1/employer/vacancies/{ctx.vacancy.id}")
    assert response.status_code == 500

    session = ctx.new_session()
    try:
        assert session.get(Vacancy, ctx.vacancy.id) is not None
        assert (
            session.scalar(
                select(func.count())
                .select_from(VacancySkillRequirement)
                .where(VacancySkillRequirement.vacancy_id == ctx.vacancy.id)
            )
            == 1
        )
        assert (
            session.scalar(
                select(func.count())
                .select_from(EmployerCandidateShortlist)
                .where(EmployerCandidateShortlist.vacancy_id == ctx.vacancy.id)
            )
            == 1
        )
        assert (
            session.scalar(
                select(func.count())
                .select_from(EmployerInterviewScorecard)
                .where(EmployerInterviewScorecard.vacancy_id == ctx.vacancy.id)
            )
            == 1
        )
    finally:
        session.close()


def test_foreign_employer_delete_returns_404(
    company_vacancy_client: tuple[TestClient, CompanyVacancyContext],
) -> None:
    client, ctx = company_vacancy_client

    response = client.delete(f"/api/v1/employer/vacancies/{ctx.foreign_vacancy.id}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "VACANCY_NOT_FOUND"

    session = ctx.new_session()
    try:
        assert session.get(Vacancy, ctx.foreign_vacancy.id) is not None
    finally:
        session.close()


def test_repeat_delete_returns_404(
    company_vacancy_client: tuple[TestClient, CompanyVacancyContext],
) -> None:
    client, ctx = company_vacancy_client

    first = client.delete(f"/api/v1/employer/vacancies/{ctx.vacancy.id}")
    assert first.status_code == 204
    second = client.delete(f"/api/v1/employer/vacancies/{ctx.vacancy.id}")
    assert second.status_code == 404
    assert second.json()["error"]["code"] == "VACANCY_NOT_FOUND"
