from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import require_candidate
from app.db.session import get_db
from app.main import app
from app.models.candidate_profile import CandidateProfile, OnboardingStatus
from app.models.user import User
from app.services.candidate_vacancies import CandidateVacancyMatch
from app.services.matching import MatchResult, SkillGroupBreakdown


def _user() -> User:
    return User(id=uuid4(), email="candidate@example.com", password_hash="hash", role="candidate", status="active")


def _profile(user_id) -> CandidateProfile:
    return CandidateProfile(id=uuid4(), user_id=user_id, display_name="Candidate", onboarding_status=OnboardingStatus.PROFILE_REQUIRED)


def _item(*, score: int, title: str, required: tuple[str, ...], preferred: tuple[str, ...], missing_required: tuple[str, ...], missing_preferred: tuple[str, ...]) -> CandidateVacancyMatch:
    vacancy = SimpleNamespace(id=uuid4(), title=title, description=f"{title} description", created_at="2026-01-01T00:00:00Z")
    return CandidateVacancyMatch(
        vacancy=vacancy,
        company_name="Acme",
        required_skills=required,
        preferred_skills=preferred,
        match=MatchResult(
            score=score,
            required=SkillGroupBreakdown(matched=tuple(skill for skill in required if skill not in missing_required), missing=missing_required),
            preferred=SkillGroupBreakdown(matched=tuple(skill for skill in preferred if skill not in missing_preferred), missing=missing_preferred),
        ),
    )


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = lambda: Mock()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_candidate_vacancy_list_is_match_sorted(client, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.v1 import candidate

    user = _user()
    profile = _profile(user.id)
    lower = _item(score=40, title="Lower match", required=("Python",), preferred=(), missing_required=("Python",), missing_preferred=())
    higher = _item(score=80, title="Higher match", required=("Python",), preferred=("Redis",), missing_required=(), missing_preferred=("Redis",))
    app.dependency_overrides[require_candidate] = lambda: user
    monkeypatch.setattr(candidate, "get_candidate_profile", lambda *_args: profile)
    monkeypatch.setattr(candidate, "list_candidate_vacancies", lambda *_args: [higher, lower])

    response = client.get("/api/v1/candidate/vacancies")

    assert response.status_code == 200
    body = response.json()
    assert [item["title"] for item in body] == ["Higher match", "Lower match"]
    assert body[0]["required_skills"] == ["Python"]
    assert body[0]["preferred_skills"] == ["Redis"]
    assert body[0]["match"]["preferred"]["missing"] == ["Redis"]


def test_candidate_vacancy_details_include_match_skills_and_shared_roadmap(client, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.v1 import candidate
    from app.schemas.roadmap import RoadmapItemResponse, RoadmapResponse

    user = _user()
    profile = _profile(user.id)
    item = _item(score=67, title="Backend role", required=("Python", "C#"), preferred=("Redis",), missing_required=("C#",), missing_preferred=("Redis",))
    app.dependency_overrides[require_candidate] = lambda: user
    monkeypatch.setattr(candidate, "get_candidate_profile", lambda *_args: profile)
    monkeypatch.setattr(candidate, "get_candidate_vacancy", lambda *_args: item)
    monkeypatch.setattr(candidate, "vacancy_roadmap", lambda *_args: RoadmapResponse(items=[RoadmapItemResponse(id="roadmap.vacancy_gap.csharp.v1", title="Build C# fundamentals", reason="Required by this vacancy.", priority="high", missing_skills=["C#"], related_skills=[])]))

    response = client.get(f"/api/v1/candidate/vacancies/{item.vacancy.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["required_skills"] == ["Python", "C#"]
    assert body["preferred_skills"] == ["Redis"]
    assert body["match"]["required"]["missing"] == ["C#"]
    assert body["match"]["preferred"]["missing"] == ["Redis"]
    assert body["roadmap"][0]["missing_skills"] == ["C#"]
