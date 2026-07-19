from collections.abc import Generator
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import require_candidate
from app.api.errors import api_error
from app.db.session import get_db
from app.main import app
from app.models.candidate_profile import CandidateProfile, OnboardingStatus
from app.models.user import User
from app.schemas.skill_passport import SkillPassportResponse, SkillPassportSkillResponse


def make_user(role: str = "candidate") -> User:
    return User(
        id=uuid4(), email="candidate@example.com", password_hash="hash", role=role, status="active"
    )


def make_profile(user_id: object | None = None) -> CandidateProfile:
    return CandidateProfile(
        id=uuid4(),
        user_id=user_id or uuid4(),
        display_name="Demo Candidate",
        onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
    )


def _passport(*names: str) -> SkillPassportResponse:
    skills = [
        SkillPassportSkillResponse(
            id=uuid4(),
            name=name,
            category="general",
            evidence_confidence=1.0,
            evidence_count=1,
            evidence=[],
        )
        for name in names
    ]
    return SkillPassportResponse(
        skills=skills, total_skills=len(skills), total_evidence=len(skills)
    )


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: object()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def authorize_candidate(user: User) -> None:
    app.dependency_overrides[require_candidate] = lambda: user


def test_roadmap_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/candidate/roadmap")
    assert response.status_code == 401


def test_roadmap_rejects_non_candidate(client: TestClient) -> None:
    app.dependency_overrides[require_candidate] = lambda: (_ for _ in ()).throw(
        api_error(403, "FORBIDDEN", "Candidate role required")
    )
    response = client.get("/api/v1/candidate/roadmap")
    assert response.status_code == 403


def test_roadmap_empty_without_profile(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import roadmap

    authorize_candidate(make_user())
    monkeypatch.setattr(roadmap, "get_candidate_profile", lambda *_args: None)

    response = client.get("/api/v1/candidate/roadmap")

    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_roadmap_empty_when_passport_has_no_matching_rules(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import roadmap

    user = make_user()
    profile = make_profile(user.id)
    authorize_candidate(user)
    monkeypatch.setattr(roadmap, "get_candidate_profile", lambda *_args: profile)
    monkeypatch.setattr(roadmap, "_build_passport", lambda *_args: _passport("Cobol"))

    response = client.get("/api/v1/candidate/roadmap")

    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_roadmap_returns_deterministic_recommendations(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import roadmap

    user = make_user()
    profile = make_profile(user.id)
    authorize_candidate(user)
    monkeypatch.setattr(roadmap, "get_candidate_profile", lambda *_args: profile)
    monkeypatch.setattr(
        roadmap,
        "_build_passport",
        lambda *_args: _passport("FastAPI", "PostgreSQL", "Python"),
    )
    app.dependency_overrides[get_db] = lambda: Mock()

    response = client.get("/api/v1/candidate/roadmap")

    assert response.status_code == 200
    body = response.json()
    ids = [item["id"] for item in body["items"]]
    assert "roadmap.docker.from_fastapi_postgresql.v1" in ids
    assert "roadmap.testing.from_python.v1" in ids

    docker = next(item for item in body["items"] if "docker" in item["id"])
    assert docker["title"]
    assert docker["reason"]
    assert docker["priority"] == "high"
    assert docker["missing_skills"] == ["Docker"]
    assert set(docker["related_skills"]) == {"FastAPI", "PostgreSQL"}
