from collections.abc import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import require_candidate
from app.api.errors import api_error
from app.db.session import get_db
from app.main import app
from app.models.candidate_profile import CandidateProfile, OnboardingStatus
from app.models.user import User
from app.schemas.dashboard import (
    CandidateDashboardResponse,
    DashboardEvidenceSummary,
    DashboardGitHubSummary,
    DashboardPassportSummary,
    DashboardRoadmapSummary,
)
from app.schemas.roadmap import RoadmapItemResponse, RoadmapResponse
from app.schemas.skill_passport import SkillPassportResponse, SkillPassportSkillResponse


def make_user() -> User:
    return User(
        id=uuid4(), email="candidate@example.com", password_hash="hash", role="candidate", status="active"
    )


def make_profile(user_id: object | None = None) -> CandidateProfile:
    return CandidateProfile(
        id=uuid4(),
        user_id=user_id or uuid4(),
        display_name="Demo Candidate",
        onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
    )


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: object()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def authorize_candidate(user: User) -> None:
    app.dependency_overrides[require_candidate] = lambda: user


def test_dashboard_requires_authentication(client: TestClient) -> None:
    assert client.get("/api/v1/candidate/dashboard").status_code == 401


def test_dashboard_rejects_non_candidate(client: TestClient) -> None:
    app.dependency_overrides[require_candidate] = lambda: (_ for _ in ()).throw(
        api_error(403, "FORBIDDEN", "Candidate role required")
    )
    response = client.get("/api/v1/candidate/dashboard")
    assert response.status_code == 403


def test_dashboard_empty_without_profile(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import dashboard

    authorize_candidate(make_user())
    monkeypatch.setattr(dashboard, "get_candidate_profile", lambda *_args: None)

    response = client.get("/api/v1/candidate/dashboard")

    assert response.status_code == 200
    assert response.json() == {
        "github": {"connected": False, "repositories": 0},
        "evidence": {"count": 0},
        "passport": {"skills": 0, "top_skills": []},
        "roadmap": {"items": 0},
    }


def test_dashboard_aggregates_existing_services(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import dashboard
    from app.services import dashboard as dashboard_service

    user = make_user()
    profile = make_profile(user.id)
    authorize_candidate(user)
    monkeypatch.setattr(dashboard, "get_candidate_profile", lambda *_args: profile)

    python_id = uuid4()
    skills = [
        SkillPassportSkillResponse(
            id=python_id,
            name=name,
            category="general",
            evidence_confidence=confidence,
            evidence_count=1,
            evidence=[],
        )
        for name, confidence in [
            ("Python", 1.0),
            ("FastAPI", 0.9),
            ("PostgreSQL", 0.8),
            ("Docker", 0.7),
            ("React", 0.6),
        ]
    ]
    passport = SkillPassportResponse(
        skills=skills, total_skills=5, total_evidence=3
    )
    roadmap = RoadmapResponse(
        items=[
            RoadmapItemResponse(
                id="roadmap.testing.from_python.v1",
                title="Testing",
                reason="reason",
                priority="high",
                missing_skills=["Testing"],
                related_skills=["Python"],
            )
        ]
        * 4
    )

    monkeypatch.setattr(dashboard_service, "build_passport", lambda *_args: passport)
    monkeypatch.setattr(
        dashboard_service, "build_roadmap_from_passport", lambda *_args: roadmap
    )

    class _ScalarResult:
        def __init__(self, value: int) -> None:
            self._value = value

        def scalar_one(self) -> int:
            return self._value

    class _Session:
        def __init__(self) -> None:
            self.calls = 0

        def execute(self, *_args: object) -> _ScalarResult:
            self.calls += 1
            # First count = repositories, second = evidence.
            return _ScalarResult(1 if self.calls == 1 else 18)

    session = _Session()
    app.dependency_overrides[get_db] = lambda: session

    response = client.get("/api/v1/candidate/dashboard")

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "github": {"connected": True, "repositories": 1},
        "evidence": {"count": 18},
        "passport": {
            "skills": 5,
            "top_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
        },
        "roadmap": {"items": 4},
    }
    # Ensure response validates against the contract schema.
    CandidateDashboardResponse.model_validate(body)
    assert isinstance(body["github"], dict)
    assert DashboardGitHubSummary.model_validate(body["github"]).connected is True
    assert DashboardEvidenceSummary.model_validate(body["evidence"]).count == 18
    assert DashboardPassportSummary.model_validate(body["passport"]).skills == 5
    assert DashboardRoadmapSummary.model_validate(body["roadmap"]).items == 4
