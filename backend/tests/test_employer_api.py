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
        "matched_details": [],
        "missing_details": [],
    }
    assert body["matches"][0]["preferred"] == {
        "matched": ["React"],
        "missing": [],
        "matched_details": [],
        "missing_details": [],
    }


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


def test_match_details_endpoint(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.v1 import employer
    from app.schemas.employer import (
        EvidenceSuggestionResponse,
        MatchDetailsCandidateResponse,
        MatchDetailsEvidenceResponse,
        MatchDetailsMatchResponse,
        MatchDetailsPassportResponse,
        MatchDetailsPassportSkillResponse,
        MatchDetailsResponse,
        MatchDetailsRoadmapItemResponse,
        MatchedSkillDetailsResponse,
        MatchedSkillEvidenceResponse,
        MatchSkillGroupResponse,
        MissingSkillDetailsResponse,
    )

    user = make_user()
    company = make_company(user.id)
    vacancy = make_vacancy(company.id)
    candidate_id = uuid4()
    docker_id = uuid4()
    authorize_employer(user)
    monkeypatch.setattr(employer, "get_employer_company", lambda *_args: company)
    monkeypatch.setattr(employer, "get_vacancy", lambda *_args: vacancy)
    monkeypatch.setattr(
        employer,
        "build_match_details",
        lambda *_args, **_kwargs: MatchDetailsResponse(
            candidate=MatchDetailsCandidateResponse(
                id=candidate_id,
                name="Ada Lovelace",
                headline="Backend Engineer",
                avatar=None,
            ),
            match=MatchDetailsMatchResponse(
                score=91,
                required=MatchSkillGroupResponse(
                    matched=["Python"],
                    missing=[],
                    matched_details=[
                        MatchedSkillDetailsResponse(
                            skill_id=uuid4(),
                            skill_name="Python",
                            evidence=[
                                MatchedSkillEvidenceResponse(
                                    id=uuid4(),
                                    source_type="resume",
                                    title="Resume: ada.pdf",
                                    verification_status="unverified",
                                    ownership_status="verified",
                                    evidence_confidence=0.87,
                                )
                            ],
                        )
                    ],
                ),
                preferred=MatchSkillGroupResponse(
                    matched=[],
                    missing=["Docker"],
                    missing_details=[
                        MissingSkillDetailsResponse(
                            skill_id=docker_id,
                            skill_name="Docker",
                            evidence_suggestions=[
                                EvidenceSuggestionResponse(category="resume_evidence"),
                                EvidenceSuggestionResponse(category="container_configuration"),
                                EvidenceSuggestionResponse(category="ci_cd_configuration"),
                            ],
                        )
                    ],
                ),
            ),
            passport=MatchDetailsPassportResponse(
                top_skills=["Python", "FastAPI"],
                skills=[
                    MatchDetailsPassportSkillResponse(
                        name="Python",
                        evidence_confidence=0.87,
                        evidence_count=3,
                        source_types=["github_repository", "resume"],
                    )
                ],
            ),
            evidence=[
                MatchDetailsEvidenceResponse(
                    source_type="resume",
                    title="Resume: ada.pdf",
                    verification_status="unverified",
                    ownership_status="verified",
                    skills=["Python", "FastAPI"],
                )
            ],
            roadmap=[
                MatchDetailsRoadmapItemResponse(
                    id="add-docker",
                    title="Add Docker evidence",
                    reason="Strengthen preferred stack",
                    priority="medium",
                    missing_skills=["Docker"],
                    related_skills=["Python"],
                )
            ],
        ),
    )

    response = client.get(
        f"/api/v1/employer/matches/{candidate_id}",
        params={"vacancy_id": str(vacancy.id)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["candidate"]["name"] == "Ada Lovelace"
    assert body["match"]["score"] == 91
    assert body["passport"]["top_skills"] == ["Python", "FastAPI"]
    assert body["passport"]["skills"] == [
        {
            "name": "Python",
            "evidence_confidence": 0.87,
            "evidence_count": 3,
            "source_types": ["github_repository", "resume"],
        }
    ]
    assert body["evidence"][0]["source_type"] == "resume"
    assert body["evidence"][0]["verification_status"] == "unverified"
    assert body["evidence"][0]["ownership_status"] == "verified"
    assert body["match"]["required"]["matched"] == ["Python"]
    assert body["match"]["required"]["matched_details"][0]["skill_name"] == "Python"
    assert set(body["match"]["required"]["matched_details"][0]["evidence"][0]) == {
        "id",
        "source_type",
        "title",
        "verification_status",
        "ownership_status",
        "evidence_confidence",
        "signal_summaries",
    }
    assert body["match"]["required"]["matched_details"][0]["evidence"][0][
        "signal_summaries"
    ] == []
    assert body["match"]["preferred"]["matched_details"] == []
    # missing stays a plain string list; missing_details is purely additive.
    assert body["match"]["preferred"]["missing"] == ["Docker"]
    assert body["match"]["required"]["missing_details"] == []
    assert body["match"]["preferred"]["missing_details"] == [
        {
            "skill_id": str(docker_id),
            "skill_name": "Docker",
            "evidence_suggestions": [
                {"category": "resume_evidence"},
                {"category": "container_configuration"},
                {"category": "ci_cd_configuration"},
            ],
        }
    ]
    assert body["roadmap"][0]["id"] == "add-docker"


def test_match_details_evidence_schema_exposes_status_fields(client: TestClient) -> None:
    schemas = client.get("/openapi.json").json()["components"]["schemas"]
    properties = schemas["MatchDetailsEvidenceResponse"]["properties"]
    assert "verification_status" in properties
    assert "ownership_status" in properties
    assert set(schemas["MatchDetailsEvidenceResponse"]["required"]) >= {
        "verification_status",
        "ownership_status",
    }


def test_match_skill_group_schema_exposes_matched_details(client: TestClient) -> None:
    schemas = client.get("/openapi.json").json()["components"]["schemas"]
    group = schemas["MatchSkillGroupResponse"]
    assert set(group["properties"]) >= {"matched", "missing", "matched_details"}
    assert group["properties"]["matched"]["type"] == "array"
    assert group["properties"]["matched"]["items"]["type"] == "string"
    assert group["properties"]["missing"]["type"] == "array"
    assert group["properties"]["missing"]["items"]["type"] == "string"
    details_ref = group["properties"]["matched_details"]["items"]["$ref"]
    assert details_ref.endswith("/MatchedSkillDetailsResponse")

    details = schemas["MatchedSkillDetailsResponse"]
    assert set(details["properties"]) == {"skill_id", "skill_name", "evidence"}
    assert details["properties"]["skill_id"]["format"] == "uuid"
    assert details["properties"]["skill_name"]["type"] == "string"
    evidence_ref = details["properties"]["evidence"]["items"]["$ref"]
    assert evidence_ref.endswith("/MatchedSkillEvidenceResponse")

    evidence = schemas["MatchedSkillEvidenceResponse"]
    assert set(evidence["properties"]) == {
        "id",
        "source_type",
        "title",
        "verification_status",
        "ownership_status",
        "evidence_confidence",
        "signal_summaries",
    }
    assert set(evidence["required"]) >= {
        "id",
        "source_type",
        "title",
        "verification_status",
        "ownership_status",
        "evidence_confidence",
    }
    # signal_summaries is optional via default_factory (may be absent from required).
    summaries = evidence["properties"]["signal_summaries"]
    assert summaries["type"] == "array"
    summary_ref = summaries["items"]["$ref"]
    assert summary_ref.endswith("/SignalSummaryResponse")

    summary = schemas["SignalSummaryResponse"]
    assert set(summary["properties"]) == {"category"}
    assert set(summary["required"]) >= {"category"}

    passport_evidence = schemas["SkillPassportEvidenceResponse"]["properties"]
    assert "signal_summaries" not in passport_evidence
    assert "context" not in passport_evidence
    assert "signals" not in passport_evidence

    verification = evidence["properties"]["verification_status"]
    ownership = evidence["properties"]["ownership_status"]
    assert "anyOf" in verification or verification.get("nullable") is True
    assert "anyOf" in ownership or ownership.get("nullable") is True


def test_match_skill_group_schema_exposes_missing_details(client: TestClient) -> None:
    schemas = client.get("/openapi.json").json()["components"]["schemas"]
    group = schemas["MatchSkillGroupResponse"]
    assert set(group["properties"]) >= {
        "matched",
        "missing",
        "matched_details",
        "missing_details",
    }
    # Binary missing semantics unchanged.
    assert group["properties"]["missing"]["type"] == "array"
    assert group["properties"]["missing"]["items"]["type"] == "string"
    # Additive array, optional via default_factory.
    missing_details = group["properties"]["missing_details"]
    assert missing_details["type"] == "array"
    assert missing_details["items"]["$ref"].endswith("/MissingSkillDetailsResponse")
    assert "missing_details" not in set(group.get("required", []))
    assert "matched_details" not in set(group.get("required", []))
    assert set(group["required"]) >= {"matched", "missing"}

    details = schemas["MissingSkillDetailsResponse"]
    assert set(details["properties"]) == {"skill_id", "skill_name", "evidence_suggestions"}
    assert set(details["required"]) == {"skill_id", "skill_name", "evidence_suggestions"}
    assert details["properties"]["skill_id"]["format"] == "uuid"
    assert details["properties"]["skill_name"]["type"] == "string"
    suggestions = details["properties"]["evidence_suggestions"]
    assert suggestions["type"] == "array"
    assert suggestions["items"]["$ref"].endswith("/EvidenceSuggestionResponse")

    suggestion = schemas["EvidenceSuggestionResponse"]
    assert set(suggestion["properties"]) == {"category"}
    assert set(suggestion["required"]) == {"category"}
    assert suggestion["properties"]["category"]["type"] == "string"

    # Safe Signal Summaries and Skill Passport contracts are untouched.
    assert set(schemas["SignalSummaryResponse"]["properties"]) == {"category"}
    assert set(schemas["MatchedSkillEvidenceResponse"]["properties"]) == {
        "id",
        "source_type",
        "title",
        "verification_status",
        "ownership_status",
        "evidence_confidence",
        "signal_summaries",
    }
    for schema_name in ("SkillPassportEvidenceResponse", "SkillPassportSkillResponse"):
        properties = schemas[schema_name]["properties"]
        assert "missing_details" not in properties
        assert "evidence_suggestions" not in properties


def test_evidence_suggestion_requires_category() -> None:
    from pydantic import ValidationError

    from app.schemas.employer import EvidenceSuggestionResponse

    with pytest.raises(ValidationError):
        EvidenceSuggestionResponse()  # type: ignore[call-arg]


def test_missing_skill_details_requires_all_fields() -> None:
    from pydantic import ValidationError

    from app.schemas.employer import MissingSkillDetailsResponse

    payload = {
        "skill_id": str(uuid4()),
        "skill_name": "Docker",
        "evidence_suggestions": [{"category": "resume_evidence"}],
    }
    for field in payload:
        incomplete = {key: value for key, value in payload.items() if key != field}
        with pytest.raises(ValidationError):
            MissingSkillDetailsResponse(**incomplete)  # type: ignore[arg-type]


def test_match_skill_group_defaults_missing_details_to_empty_list() -> None:
    from app.schemas.employer import MatchSkillGroupResponse

    group = MatchSkillGroupResponse(matched=["Python"], missing=["Docker"])
    assert group.missing_details == []
    assert group.matched_details == []
    assert group.model_dump()["missing_details"] == []


def test_signal_summary_requires_category() -> None:
    from pydantic import ValidationError

    from app.schemas.employer import SignalSummaryResponse

    with pytest.raises(ValidationError):
        SignalSummaryResponse()  # type: ignore[call-arg]



@pytest.mark.parametrize("missing_field", ["verification_status", "ownership_status"])
def test_match_details_evidence_requires_status_keys(missing_field: str) -> None:
    from pydantic import ValidationError

    from app.schemas.employer import MatchDetailsEvidenceResponse

    payload = {
        "source_type": "resume",
        "title": "Resume: ada.pdf",
        "verification_status": None,
        "ownership_status": None,
        "skills": ["Python"],
    }
    del payload[missing_field]
    with pytest.raises(ValidationError):
        MatchDetailsEvidenceResponse(**payload)


def test_match_details_evidence_accepts_explicit_null_statuses() -> None:
    from app.schemas.employer import MatchDetailsEvidenceResponse

    evidence = MatchDetailsEvidenceResponse(
        source_type="resume",
        title="Resume: ada.pdf",
        verification_status=None,
        ownership_status=None,
        skills=["Python"],
    )
    assert evidence.verification_status is None
    assert evidence.ownership_status is None


def test_match_details_requires_vacancy_query(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import employer

    user = make_user()
    authorize_employer(user)
    monkeypatch.setattr(employer, "get_employer_company", lambda *_args: make_company(user.id))

    response = client.get(f"/api/v1/employer/matches/{uuid4()}")
    assert response.status_code == 422


def test_match_details_candidate_not_found(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import employer
    from app.services.match_details import MatchDetailsCandidateNotFoundError

    user = make_user()
    company = make_company(user.id)
    vacancy = make_vacancy(company.id)
    authorize_employer(user)
    monkeypatch.setattr(employer, "get_employer_company", lambda *_args: company)
    monkeypatch.setattr(employer, "get_vacancy", lambda *_args: vacancy)

    def missing(*_args: object, **_kwargs: object) -> None:
        raise MatchDetailsCandidateNotFoundError

    monkeypatch.setattr(employer, "build_match_details", missing)

    response = client.get(
        f"/api/v1/employer/matches/{uuid4()}",
        params={"vacancy_id": str(vacancy.id)},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CANDIDATE_NOT_FOUND"
