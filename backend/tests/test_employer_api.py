from collections.abc import Generator
from datetime import UTC, datetime
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import require_employer
from app.api.errors import api_error
from app.db.session import get_db
from app.main import app
from app.models.employer_profile import EmployerProfile
from app.models.skill import Skill
from app.models.user import User
from app.models.vacancy import Vacancy
from app.models.vacancy_skill_requirement import VacancySkillRequirement
from app.services.employer import (
    EmployerCompanyAlreadyExistsError,
    SkillNotAvailableError,
    VacancyRequirementConflictError,
    VacancyRequirementNotFoundError,
)


def make_user(role: str = "employer") -> User:
    return User(
        id=uuid4(), email="employer@example.com", password_hash="hash", role=role, status="active"
    )


def make_company(user_id: object | None = None) -> EmployerProfile:
    return EmployerProfile(
        id=uuid4(),
        user_id=user_id or uuid4(),
        company_name="Acme Corp",
        website="https://acme.example",
        description="We hire builders",
        created_at=datetime.now(UTC),
    )


def make_vacancy(employer_id: object | None = None) -> Vacancy:
    return Vacancy(
        id=uuid4(),
        employer_id=employer_id or uuid4(),
        title="Junior Backend Engineer",
        description="Build APIs with FastAPI",
        status="open",
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: object()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def authorize_employer(user: User) -> None:
    app.dependency_overrides[require_employer] = lambda: user


def test_employer_endpoints_require_authentication(client: TestClient) -> None:
    assert client.get("/api/v1/employer/company").status_code == 401
    assert client.get("/api/v1/employer/vacancies").status_code == 401


def test_employer_endpoints_reject_candidate(client: TestClient) -> None:
    app.dependency_overrides[require_employer] = lambda: (_ for _ in ()).throw(
        api_error(403, "FORBIDDEN", "Employer role required")
    )
    assert client.get("/api/v1/employer/company").status_code == 403


def test_get_company_not_found(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.v1 import employer

    authorize_employer(make_user())
    monkeypatch.setattr(employer, "get_employer_company", lambda *_args: None)

    response = client.get("/api/v1/employer/company")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "EMPLOYER_COMPANY_NOT_FOUND"


def test_create_and_get_company(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.v1 import employer

    user = make_user()
    company = make_company(user.id)
    authorize_employer(user)
    monkeypatch.setattr(employer, "create_employer_company", lambda *_args, **_kwargs: company)
    monkeypatch.setattr(employer, "get_employer_company", lambda *_args: company)

    create_response = client.post(
        "/api/v1/employer/company",
        json={
            "company_name": "Acme Corp",
            "website": "https://acme.example",
            "description": "We hire builders",
        },
    )
    assert create_response.status_code == 201
    assert create_response.json()["company_name"] == "Acme Corp"
    assert create_response.json()["website"] == "https://acme.example"

    get_response = client.get("/api/v1/employer/company")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == str(company.id)


def test_create_company_conflict(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.v1 import employer

    authorize_employer(make_user())

    def create(*_args: object, **_kwargs: object) -> EmployerProfile:
        raise EmployerCompanyAlreadyExistsError

    monkeypatch.setattr(employer, "create_employer_company", create)

    response = client.post(
        "/api/v1/employer/company",
        json={"company_name": "Acme Corp"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EMPLOYER_COMPANY_ALREADY_EXISTS"


def test_vacancies_require_company(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.v1 import employer

    authorize_employer(make_user())
    monkeypatch.setattr(employer, "get_employer_company", lambda *_args: None)

    response = client.get("/api/v1/employer/vacancies")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EMPLOYER_COMPANY_REQUIRED"


def test_list_create_and_get_vacancy(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.v1 import employer

    user = make_user()
    company = make_company(user.id)
    vacancy = make_vacancy(company.id)
    authorize_employer(user)
    monkeypatch.setattr(employer, "get_employer_company", lambda *_args: company)
    monkeypatch.setattr(employer, "list_vacancies", lambda *_args: [vacancy])
    monkeypatch.setattr(employer, "create_vacancy", lambda *_args, **_kwargs: vacancy)
    monkeypatch.setattr(employer, "get_vacancy", lambda *_args: vacancy)
    app.dependency_overrides[get_db] = lambda: Mock()

    list_response = client.get("/api/v1/employer/vacancies")
    assert list_response.status_code == 200
    assert list_response.json()[0]["title"] == "Junior Backend Engineer"
    assert list_response.json()[0]["status"] == "open"

    create_response = client.post(
        "/api/v1/employer/vacancies",
        json={
            "title": "Junior Backend Engineer",
            "description": "Build APIs with FastAPI",
            "status": "open",
        },
    )
    assert create_response.status_code == 201
    assert create_response.json()["id"] == str(vacancy.id)

    detail_response = client.get(f"/api/v1/employer/vacancies/{vacancy.id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["description"] == "Build APIs with FastAPI"
    assert "created_at" in detail_response.json()


def test_get_vacancy_not_found(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.v1 import employer

    user = make_user()
    company = make_company(user.id)
    authorize_employer(user)
    monkeypatch.setattr(employer, "get_employer_company", lambda *_args: company)
    monkeypatch.setattr(employer, "get_vacancy", lambda *_args: None)

    response = client.get(f"/api/v1/employer/vacancies/{uuid4()}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "VACANCY_NOT_FOUND"


def make_skill(name: str = "Python") -> Skill:
    return Skill(
        id=uuid4(),
        canonical_name=name,
        normalized_name=name.lower(),
        category="language",
        deprecated=False,
        ontology_version="v1",
    )


def make_requirement(
    vacancy_id: object | None = None, skill: Skill | None = None
) -> VacancySkillRequirement:
    return VacancySkillRequirement(
        id=uuid4(),
        vacancy_id=vacancy_id or uuid4(),
        skill_id=(skill or make_skill()).id,
        requirement_type="required",
    )


def test_list_skills_for_requirement_picker(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import employer

    authorize_employer(make_user())
    skill = make_skill("TypeScript")
    monkeypatch.setattr(employer, "list_available_skills", lambda *_args: [skill])

    response = client.get("/api/v1/employer/skills")

    assert response.status_code == 200
    assert response.json() == [
        {"id": str(skill.id), "name": "TypeScript", "category": "language"}
    ]


def test_vacancy_requirements_crud(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.v1 import employer

    user = make_user()
    company = make_company(user.id)
    vacancy = make_vacancy(company.id)
    skill = make_skill("Python")
    requirement = make_requirement(vacancy.id, skill)
    authorize_employer(user)
    monkeypatch.setattr(employer, "get_employer_company", lambda *_args: company)
    monkeypatch.setattr(employer, "get_vacancy", lambda *_args: vacancy)
    monkeypatch.setattr(
        employer, "list_vacancy_requirements", lambda *_args: [(requirement, skill)]
    )
    monkeypatch.setattr(
        employer, "add_vacancy_requirement", lambda *_args, **_kwargs: (requirement, skill)
    )

    deleted: list[UUID] = []

    def delete(_session: object, owned_vacancy_id: UUID, requirement_id: UUID) -> None:
        deleted.append(requirement_id)
        assert owned_vacancy_id == vacancy.id

    monkeypatch.setattr(employer, "delete_vacancy_requirement", delete)

    list_response = client.get(f"/api/v1/employer/vacancies/{vacancy.id}/requirements")
    assert list_response.status_code == 200
    assert list_response.json()[0]["skill_name"] == "Python"
    assert list_response.json()[0]["requirement_type"] == "required"

    create_response = client.post(
        f"/api/v1/employer/vacancies/{vacancy.id}/requirements",
        json={"skill_id": str(skill.id), "requirement_type": "required"},
    )
    assert create_response.status_code == 201
    assert create_response.json()["skill_id"] == str(skill.id)

    delete_response = client.delete(
        f"/api/v1/employer/vacancies/{vacancy.id}/requirements/{requirement.id}"
    )
    assert delete_response.status_code == 204
    assert deleted == [requirement.id]


def test_add_requirement_rejects_unknown_skill_and_conflicts(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import employer

    user = make_user()
    company = make_company(user.id)
    vacancy = make_vacancy(company.id)
    authorize_employer(user)
    monkeypatch.setattr(employer, "get_employer_company", lambda *_args: company)
    monkeypatch.setattr(employer, "get_vacancy", lambda *_args: vacancy)

    def missing(*_args: object, **_kwargs: object) -> tuple[object, object]:
        raise SkillNotAvailableError

    monkeypatch.setattr(employer, "add_vacancy_requirement", missing)
    missing_response = client.post(
        f"/api/v1/employer/vacancies/{vacancy.id}/requirements",
        json={"skill_id": str(uuid4()), "requirement_type": "preferred"},
    )
    assert missing_response.status_code == 404
    assert missing_response.json()["error"]["code"] == "SKILL_NOT_FOUND"

    def conflict(*_args: object, **_kwargs: object) -> tuple[object, object]:
        raise VacancyRequirementConflictError

    monkeypatch.setattr(employer, "add_vacancy_requirement", conflict)
    conflict_response = client.post(
        f"/api/v1/employer/vacancies/{vacancy.id}/requirements",
        json={"skill_id": str(uuid4()), "requirement_type": "preferred"},
    )
    assert conflict_response.status_code == 409
    assert conflict_response.json()["error"]["code"] == "VACANCY_REQUIREMENT_CONFLICT"


def test_delete_requirement_not_found(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import employer

    user = make_user()
    company = make_company(user.id)
    vacancy = make_vacancy(company.id)
    authorize_employer(user)
    monkeypatch.setattr(employer, "get_employer_company", lambda *_args: company)
    monkeypatch.setattr(employer, "get_vacancy", lambda *_args: vacancy)

    def missing(*_args: object) -> None:
        raise VacancyRequirementNotFoundError

    monkeypatch.setattr(employer, "delete_vacancy_requirement", missing)
    response = client.delete(
        f"/api/v1/employer/vacancies/{vacancy.id}/requirements/{uuid4()}"
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "VACANCY_REQUIREMENT_NOT_FOUND"


def test_vacancy_matches_endpoint(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.v1 import employer
    from app.services.employer import VacancyCandidateMatch
    from app.services.matching import MatchResult, SkillGroupBreakdown

    user = make_user()
    company = make_company(user.id)
    vacancy = make_vacancy(company.id)
    authorize_employer(user)
    monkeypatch.setattr(employer, "get_employer_company", lambda *_args: company)
    monkeypatch.setattr(employer, "get_vacancy", lambda *_args: vacancy)
    monkeypatch.setattr(
        employer,
        "list_vacancy_matches",
        lambda *_args: [
            VacancyCandidateMatch(
                candidate_id=uuid4(),
                candidate_name="Ada Lovelace",
                result=MatchResult(
                    score=85,
                    required=SkillGroupBreakdown(matched=("Python",), missing=("Docker",)),
                    preferred=SkillGroupBreakdown(matched=("React",), missing=()),
                ),
            )
        ],
    )

    response = client.get(f"/api/v1/employer/vacancies/{vacancy.id}/matches")

    assert response.status_code == 200
    body = response.json()
    assert body["matches"][0]["candidate_name"] == "Ada Lovelace"
    assert body["matches"][0]["score"] == 85
    assert body["matches"][0]["required"] == {
        "matched": ["Python"],
        "missing": ["Docker"],
    }
    assert body["matches"][0]["preferred"] == {"matched": ["React"], "missing": []}


def test_vacancy_matches_requires_owned_vacancy(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import employer

    user = make_user()
    company = make_company(user.id)
    authorize_employer(user)
    monkeypatch.setattr(employer, "get_employer_company", lambda *_args: company)
    monkeypatch.setattr(employer, "get_vacancy", lambda *_args: None)

    response = client.get(f"/api/v1/employer/vacancies/{uuid4()}/matches")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "VACANCY_NOT_FOUND"
