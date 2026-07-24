from collections.abc import Generator
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import require_candidate
from app.api.errors import api_error
from app.db.session import get_db
from app.main import app
from app.models.candidate_profile import CandidateProfile, OnboardingStatus
from app.models.evidence_unit import EvidenceUnit
from app.models.github_repository import GitHubRepository
from app.models.skill import Skill
from app.models.user import User
from app.schemas.skill_passport import SkillPassportEvidenceResponse


def make_user(role: str = "candidate") -> User:
    return User(
        id=uuid4(), email="candidate@example.com", password_hash="hash", role=role, status="active"
    )


def make_profile(user_id: UUID | None = None) -> CandidateProfile:
    return CandidateProfile(
        id=uuid4(),
        user_id=user_id or uuid4(),
        display_name="Demo Candidate",
        onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
    )


def make_skill(
    *,
    name: str,
    category: str = "language",
    deprecated: bool = False,
) -> Skill:
    return Skill(
        id=uuid4(),
        canonical_name=name,
        normalized_name=name.lower(),
        category=category,
        deprecated=deprecated,
        ontology_version="v1",
    )


def make_evidence(
    *,
    candidate_id: UUID,
    title: str,
    source_type: str = "github_repository",
    source_reference: str = "https://github.com/demo/repo",
    verification_status: str | None = "source_reachable",
    ownership_status: str | None = "unverified",
) -> EvidenceUnit:
    return EvidenceUnit(
        id=uuid4(),
        candidate_id=candidate_id,
        source_type=source_type,
        source_reference=source_reference,
        title=title,
        description=f"Description for {title}",
        observed_at=datetime.now(UTC),
        verification_status=verification_status,
        ownership_status=ownership_status,
        strength_score=Decimal("1.00"),
    )


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: object()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def authorize_candidate(user: User) -> None:
    app.dependency_overrides[require_candidate] = lambda: user


def _session_returning_rows(
    rows: list[tuple[Skill, EvidenceUnit, object]],
    repositories: list[GitHubRepository] | None = None,
) -> Mock:
    session = Mock()
    normalized_rows = [
        (
            skill,
            evidence,
            context
            if isinstance(context, dict)
            else {
                "signals": [
                    {
                        "type": (
                            "source_api_call" if float(context) >= 0.9 else "source_import"
                        ),
                        "path": f"{skill.id}.py",
                    }
                ]
            },
        )
        for skill, evidence, context in rows
    ]
    session.execute.side_effect = (
        SimpleNamespace(all=lambda: normalized_rows),
        SimpleNamespace(scalars=lambda: iter(repositories or [])),
    )
    return session


def test_skill_passport_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/candidate/skill-passport")
    assert response.status_code == 401


def test_skill_passport_rejects_non_candidate(client: TestClient) -> None:
    app.dependency_overrides[require_candidate] = lambda: (_ for _ in ()).throw(
        api_error(403, "FORBIDDEN", "Candidate role required")
    )
    response = client.get("/api/v1/candidate/skill-passport")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_skill_passport_empty_when_profile_missing(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import skill_passport

    authorize_candidate(make_user())
    monkeypatch.setattr(skill_passport, "get_candidate_profile", lambda *_args: None)

    response = client.get("/api/v1/candidate/skill-passport")

    assert response.status_code == 200
    assert response.json() == {"skills": [], "total_skills": 0, "total_evidence": 0}


def test_skill_passport_empty_when_no_links(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import skill_passport

    user = make_user()
    profile = make_profile(user.id)
    authorize_candidate(user)
    monkeypatch.setattr(skill_passport, "get_candidate_profile", lambda *_args: profile)
    app.dependency_overrides[get_db] = lambda: _session_returning_rows([])

    response = client.get("/api/v1/candidate/skill-passport")

    assert response.status_code == 200
    assert response.json() == {"skills": [], "total_skills": 0, "total_evidence": 0}


def test_skill_passport_aggregates_skills_evidence_and_totals(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import skill_passport

    user = make_user()
    profile = make_profile(user.id)
    python = make_skill(name="Python")
    typescript = make_skill(name="TypeScript", category="language")
    evidence_a = make_evidence(candidate_id=profile.id, title="Repo A")
    evidence_b = make_evidence(
        candidate_id=profile.id,
        title="Repo B",
        source_reference="https://github.com/demo/other",
    )
    rows = [
        (python, evidence_a, Decimal("0.80")),
        (python, evidence_b, Decimal("0.60")),
        (typescript, evidence_a, Decimal("0.90")),
    ]

    authorize_candidate(user)
    monkeypatch.setattr(skill_passport, "get_candidate_profile", lambda *_args: profile)
    app.dependency_overrides[get_db] = lambda: _session_returning_rows(rows)

    response = client.get("/api/v1/candidate/skill-passport")

    assert response.status_code == 200
    body = response.json()
    assert body["total_skills"] == 2
    assert body["total_evidence"] == 2
    skills = {skill["name"]: skill for skill in body["skills"]}
    typescript_skill = skills["TypeScript"]
    assert 0 < typescript_skill["evidence_confidence"] <= 0.95
    assert typescript_skill["evidence_count"] == 1
    assert 0 < typescript_skill["evidence"][0]["evidence_confidence"] <= 0.95
    assert "confidence" not in typescript_skill
    assert "confidence" not in typescript_skill["evidence"][0]

    python_skill = skills["Python"]
    assert 0 < python_skill["evidence_confidence"] <= 0.95
    assert python_skill["evidence_count"] == 2
    assert [item["title"] for item in python_skill["evidence"]] == ["Repo A", "Repo B"]
    assert all(0 < item["evidence_confidence"] <= 0.95 for item in python_skill["evidence"])


def test_skill_passport_returns_repository_only_confidence_breakdown(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import skill_passport

    user = make_user()
    profile = make_profile(user.id)
    react = make_skill(name="React", category="frontend")
    repository_a_url = "https://github.com/demo/frontend"
    repository_b_url = "https://github.com/demo/config"
    repository_a = GitHubRepository(id=uuid4(), candidate_id=profile.id, repository_url=repository_a_url)
    repository_b = GitHubRepository(id=uuid4(), candidate_id=profile.id, repository_url=repository_b_url)
    evidence_a = make_evidence(
        candidate_id=profile.id,
        title="Frontend source",
        source_reference=repository_a_url,
    )
    evidence_b = make_evidence(
        candidate_id=profile.id,
        title="Package manifest",
        source_reference=repository_b_url,
    )
    rows = [
        (
            react,
            evidence_a,
            {
                "signals": [
                    {"type": "source_import", "path": "src/App.tsx"},
                    {"type": "source_function_usage", "path": "src/components/App.tsx"},
                    {"type": "test_usage", "path": "tests/App.test.tsx"},
                ]
            },
        ),
        (
            react,
            evidence_b,
            {"signals": [{"type": "dependency_manifest", "manifest": "package.json"}]},
        ),
    ]

    authorize_candidate(user)
    monkeypatch.setattr(skill_passport, "get_candidate_profile", lambda *_args: profile)
    app.dependency_overrides[get_db] = lambda: _session_returning_rows(
        rows, [repository_a, repository_b]
    )

    response = client.get("/api/v1/candidate/skill-passport")

    assert response.status_code == 200
    skill = response.json()["skills"][0]
    repositories = {item["repository_name"]: item for item in skill["github_repositories"]}
    assert set(repositories) == {"demo/frontend", "demo/config"}
    assert all(isinstance(item["repository_confidence"], int) for item in repositories.values())
    assert all(0 <= item["repository_confidence"] <= 95 for item in repositories.values())
    assert repositories["demo/frontend"]["repository_confidence"] > repositories["demo/config"]["repository_confidence"]
    assert skill["evidence_confidence"] != sum(
        item["repository_confidence"] for item in repositories.values()
    ) / 100


def test_skill_passport_deduplicates_multiple_links_for_same_skill_evidence_pair(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import skill_passport

    user = make_user()
    profile = make_profile(user.id)
    python = make_skill(name="Python")
    evidence = make_evidence(candidate_id=profile.id, title="Demo repo")
    rows = [
        (python, evidence, Decimal("0.40")),
        (python, evidence, Decimal("0.95")),
        (python, evidence, Decimal("0.70")),
    ]

    authorize_candidate(user)
    monkeypatch.setattr(skill_passport, "get_candidate_profile", lambda *_args: profile)
    app.dependency_overrides[get_db] = lambda: _session_returning_rows(rows)

    response = client.get("/api/v1/candidate/skill-passport")

    assert response.status_code == 200
    body = response.json()
    assert body["total_skills"] == 1
    assert body["total_evidence"] == 1
    skill = body["skills"][0]
    assert skill["evidence_count"] == 1
    assert 0 < skill["evidence_confidence"] <= 0.95
    assert 0 < skill["evidence"][0]["evidence_confidence"] <= 0.95


def test_skill_passport_excludes_deprecated_skills(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import skill_passport

    user = make_user()
    profile = make_profile(user.id)
    active = make_skill(name="Python")
    deprecated = make_skill(name="CoffeeScript", deprecated=True)
    evidence = make_evidence(candidate_id=profile.id, title="Demo repo")
    rows = [
        (active, evidence, Decimal("1.00")),
        (deprecated, evidence, Decimal("1.00")),
    ]

    authorize_candidate(user)
    monkeypatch.setattr(skill_passport, "get_candidate_profile", lambda *_args: profile)
    app.dependency_overrides[get_db] = lambda: _session_returning_rows(rows)

    response = client.get("/api/v1/candidate/skill-passport")

    assert response.status_code == 200
    body = response.json()
    assert body["total_skills"] == 1
    assert body["skills"][0]["name"] == "Python"
    assert all(skill["name"] != "CoffeeScript" for skill in body["skills"])


def test_skill_passport_isolates_candidate_data(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import skill_passport

    owner = make_user()
    owner_profile = make_profile(owner.id)
    other = make_user()
    other_profile = make_profile(other.id)
    skill = make_skill(name="Python")
    owner_evidence = make_evidence(candidate_id=owner_profile.id, title="Owner repo")

    authorize_candidate(other)
    monkeypatch.setattr(skill_passport, "get_candidate_profile", lambda *_args: other_profile)
    # Session returns no rows for the other candidate — owner evidence is not queried.
    app.dependency_overrides[get_db] = lambda: _session_returning_rows([])

    response = client.get("/api/v1/candidate/skill-passport")

    assert response.status_code == 200
    assert response.json() == {"skills": [], "total_skills": 0, "total_evidence": 0}

    authorize_candidate(owner)
    monkeypatch.setattr(skill_passport, "get_candidate_profile", lambda *_args: owner_profile)
    app.dependency_overrides[get_db] = lambda: _session_returning_rows(
        [(skill, owner_evidence, Decimal("1.00"))]
    )

    owner_response = client.get("/api/v1/candidate/skill-passport")
    assert owner_response.status_code == 200
    assert owner_response.json()["total_skills"] == 1
    assert owner_response.json()["skills"][0]["name"] == "Python"


def test_skill_passport_sorts_by_evidence_confidence_then_name(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import skill_passport

    user = make_user()
    profile = make_profile(user.id)
    alpha = make_skill(name="Alpha")
    beta = make_skill(name="Beta")
    gamma = make_skill(name="Gamma")
    evidence = make_evidence(candidate_id=profile.id, title="Shared")
    rows = [
        (alpha, evidence, Decimal("0.50")),
        (gamma, evidence, Decimal("0.90")),
        (beta, evidence, Decimal("0.90")),
    ]

    authorize_candidate(user)
    monkeypatch.setattr(skill_passport, "get_candidate_profile", lambda *_args: profile)
    app.dependency_overrides[get_db] = lambda: _session_returning_rows(rows)

    response = client.get("/api/v1/candidate/skill-passport")

    assert response.status_code == 200
    names = [skill["name"] for skill in response.json()["skills"]]
    assert names == ["Beta", "Gamma", "Alpha"]


def test_skill_passport_exposes_resume_evidence_verification_and_ownership(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import skill_passport

    user = make_user()
    profile = make_profile(user.id)
    python = make_skill(name="Python")
    evidence = make_evidence(
        candidate_id=profile.id,
        title="Resume: ada.pdf",
        source_type="resume",
        source_reference=str(uuid4()),
        verification_status="unverified",
        ownership_status="verified",
    )

    authorize_candidate(user)
    monkeypatch.setattr(skill_passport, "get_candidate_profile", lambda *_args: profile)
    app.dependency_overrides[get_db] = lambda: _session_returning_rows(
        [(python, evidence, Decimal("1.00"))]
    )

    response = client.get("/api/v1/candidate/skill-passport")

    assert response.status_code == 200
    evidence_item = response.json()["skills"][0]["evidence"][0]
    assert evidence_item["verification_status"] == "unverified"
    assert evidence_item["ownership_status"] == "verified"


def test_skill_passport_exposes_github_evidence_verification_and_ownership(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import skill_passport

    user = make_user()
    profile = make_profile(user.id)
    python = make_skill(name="Python")
    evidence = make_evidence(
        candidate_id=profile.id,
        title="Repo A",
        source_type="github_repository",
        verification_status="source_reachable",
        ownership_status="unverified",
    )

    authorize_candidate(user)
    monkeypatch.setattr(skill_passport, "get_candidate_profile", lambda *_args: profile)
    app.dependency_overrides[get_db] = lambda: _session_returning_rows(
        [(python, evidence, Decimal("1.00"))]
    )

    response = client.get("/api/v1/candidate/skill-passport")

    assert response.status_code == 200
    evidence_item = response.json()["skills"][0]["evidence"][0]
    assert evidence_item["verification_status"] == "source_reachable"
    assert evidence_item["ownership_status"] == "unverified"


def test_skill_passport_copies_statuses_from_model_not_source_type(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import skill_passport

    user = make_user()
    profile = make_profile(user.id)
    python = make_skill(name="Python")
    # Non-standard but valid combination: a GitHub-sourced unit that carries
    # an issuer-verified status. If statuses were derived from source_type this
    # combination could not survive the round-trip.
    evidence = make_evidence(
        candidate_id=profile.id,
        title="Repo A",
        source_type="github_repository",
        verification_status="issuer_verified",
        ownership_status="verified",
    )

    authorize_candidate(user)
    monkeypatch.setattr(skill_passport, "get_candidate_profile", lambda *_args: profile)
    app.dependency_overrides[get_db] = lambda: _session_returning_rows(
        [(python, evidence, Decimal("1.00"))]
    )

    response = client.get("/api/v1/candidate/skill-passport")

    assert response.status_code == 200
    evidence_item = response.json()["skills"][0]["evidence"][0]
    assert evidence_item["verification_status"] == "issuer_verified"
    assert evidence_item["ownership_status"] == "verified"
    # Existing evidence fields are unchanged and additive-only.
    assert evidence_item["source_type"] == "github_repository"
    assert evidence_item["source_reference"] == "https://github.com/demo/repo"
    assert 0 < evidence_item["evidence_confidence"] <= 0.95


def test_skill_passport_evidence_schema_exposes_status_fields(client: TestClient) -> None:
    schemas = client.get("/openapi.json").json()["components"]["schemas"]
    properties = schemas["SkillPassportEvidenceResponse"]["properties"]
    assert "verification_status" in properties
    assert "ownership_status" in properties
    assert set(schemas["SkillPassportEvidenceResponse"]["required"]) >= {
        "verification_status",
        "ownership_status",
    }


@pytest.mark.parametrize("missing_field", ["verification_status", "ownership_status"])
def test_skill_passport_evidence_requires_status_keys(missing_field: str) -> None:
    from pydantic import ValidationError

    payload = {
        "id": uuid4(),
        "title": None,
        "description": None,
        "source_type": "resume",
        "source_reference": None,
        "verification_status": None,
        "ownership_status": None,
        "evidence_confidence": 0.5,
    }
    del payload[missing_field]
    with pytest.raises(ValidationError):
        SkillPassportEvidenceResponse(**payload)


def test_skill_passport_evidence_accepts_explicit_null_statuses() -> None:
    evidence = SkillPassportEvidenceResponse(
        id=uuid4(),
        title=None,
        description=None,
        source_type="resume",
        source_reference=None,
        verification_status=None,
        ownership_status=None,
        evidence_confidence=0.5,
    )
    assert evidence.verification_status is None
    assert evidence.ownership_status is None
