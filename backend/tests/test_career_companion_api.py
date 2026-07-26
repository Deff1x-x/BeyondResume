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
from app.schemas.career_companion import CareerCompanionPlanResponse
from app.schemas.roadmap import RoadmapResponse


def make_user(role: str = "candidate") -> User:
    return User(
        id=uuid4(),
        email=f"{role}@example.com",
        password_hash="hash",
        role=role,
        status="active",
    )


def make_profile(user_id=None) -> CandidateProfile:
    return CandidateProfile(
        id=uuid4(),
        user_id=user_id or uuid4(),
        display_name="Demo Candidate",
        onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
        target_role="Backend Developer",
    )


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: Mock()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def authorize_candidate(user: User) -> None:
    app.dependency_overrides[require_candidate] = lambda: user


def test_companion_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/candidate/career-companion")
    assert response.status_code == 401


def test_companion_rejects_employer(client: TestClient) -> None:
    app.dependency_overrides[require_candidate] = lambda: (_ for _ in ()).throw(
        api_error(403, "FORBIDDEN", "Candidate role required")
    )
    response = client.get("/api/v1/candidate/career-companion")
    assert response.status_code == 403


def test_companion_requires_profile(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.v1 import career_companion

    authorize_candidate(make_user())
    monkeypatch.setattr(career_companion, "get_candidate_profile", lambda *_a, **_k: None)
    response = client.get("/api/v1/candidate/career-companion")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CANDIDATE_PROFILE_REQUIRED"


def test_patch_action_rejects_foreign_action(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import career_companion
    from app.services.career_companion.plan_service import CareerCompanionError

    user = make_user()
    profile = make_profile(user.id)
    authorize_candidate(user)
    monkeypatch.setattr(career_companion, "get_candidate_profile", lambda *_a, **_k: profile)

    def _raise(*_a, **_k):
        raise CareerCompanionError("Action not found", code="ACTION_NOT_FOUND")

    monkeypatch.setattr(career_companion, "patch_action_status", _raise)
    response = client.patch(
        f"/api/v1/candidate/career-companion/actions/{uuid4()}",
        json={"status": "accepted"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ACTION_NOT_FOUND"


def test_patch_rejects_completed_status_at_schema(client: TestClient) -> None:
    authorize_candidate(make_user())
    response = client.patch(
        f"/api/v1/candidate/career-companion/actions/{uuid4()}",
        json={"status": "completed"},
    )
    assert response.status_code == 422


def test_legacy_roadmap_does_not_call_generate(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import roadmap
    from app.schemas.skill_passport import SkillPassportResponse

    user = make_user()
    profile = make_profile(user.id)
    authorize_candidate(user)
    monkeypatch.setattr(roadmap, "get_candidate_profile", lambda *_a, **_k: profile)
    monkeypatch.setattr(roadmap, "get_active_plan", lambda *_a, **_k: None)
    monkeypatch.setattr(
        roadmap,
        "_build_passport",
        lambda *_a, **_k: SkillPassportResponse(skills=[], total_skills=0, total_evidence=0),
    )
    called = {"generate": False}

    def _boom(*_a, **_k):
        called["generate"] = True
        raise AssertionError("roadmap must not generate companion plans")

    monkeypatch.setattr(
        "app.services.career_companion.plan_service.generate_plan",
        _boom,
        raising=False,
    )

    response = client.get("/api/v1/candidate/roadmap")
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    RoadmapResponse.model_validate(body)
    assert called["generate"] is False


def test_legacy_roadmap_adapts_fix_now_only(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import roadmap
    from types import SimpleNamespace

    user = make_user()
    profile = make_profile(user.id)
    authorize_candidate(user)
    monkeypatch.setattr(roadmap, "get_candidate_profile", lambda *_a, **_k: profile)

    plan = SimpleNamespace(
        actions=[
            SimpleNamespace(
                id=uuid4(),
                horizon="fix_now",
                title="Fix Docker gap",
                why_it_matters="Required",
                priority_score=70,
                skills=[SimpleNamespace(skill_name="Docker", role="gap")],
            ),
            SimpleNamespace(
                id=uuid4(),
                horizon="build_next",
                title="Should not appear",
                why_it_matters="x",
                priority_score=40,
                skills=[],
            ),
        ]
    )
    monkeypatch.setattr(roadmap, "get_active_plan", lambda *_a, **_k: plan)

    response = client.get("/api/v1/candidate/roadmap")
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["title"] == "Fix Docker gap"
    RoadmapResponse.model_validate(body)


def test_generate_target_role_payload_contract(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """UI sends mode=target_role + target_role; backend must accept and return a plan."""
    from app.api.v1 import career_companion
    from types import SimpleNamespace
    from uuid import uuid4

    user = make_user()
    profile = make_profile(user.id)
    authorize_candidate(user)
    monkeypatch.setattr(career_companion, "get_candidate_profile", lambda *_a, **_k: profile)

    captured: dict = {}

    def _generate(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            id=uuid4(),
            mode="target_role",
            target_vacancy_id=None,
            target_role="Backend Developer",
            status="active",
            generation_mode="fallback",
            summary={"headline": "ok"},
            current_position={
                "goal_label": "Backend Developer",
                "verified_skills": [],
                "missing_required_skills": ["Docker"],
                "readiness": "not_ready",
                "strongest_projects": [],
            },
            actions=[],
            progress_events=[],
            chat_messages=[],
        )

    monkeypatch.setattr(career_companion, "generate_plan", lambda *_a, **kwargs: _generate(**kwargs))
    monkeypatch.setattr(
        career_companion,
        "build_companion_context",
        lambda *_a, **_k: SimpleNamespace(projects=[], vacancy_matches=[]),
    )
    monkeypatch.setattr(career_companion, "get_active_plan", lambda *_a, **_k: _generate())

    response = client.post(
        "/api/v1/candidate/career-companion/generate",
        json={
            "mode": "target_role",
            "target_vacancy_id": None,
            "target_role": "Backend Developer",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "target_role"
    assert body["target_role"] == "Backend Developer"
    assert body["generation_mode"] in {"live", "mock", "fallback"}
    assert captured["mode"] == "target_role"
    assert captured["target_role"] == "Backend Developer"
    assert captured["prefer_ai"] is True
    CareerCompanionPlanResponse.model_validate(body)


def test_generate_forwards_each_mode_without_stale_target_role(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Each selector mode must reach the service with only its own target field."""
    from app.api.v1 import career_companion
    from types import SimpleNamespace

    user = make_user()
    profile = make_profile(user.id)
    authorize_candidate(user)
    monkeypatch.setattr(career_companion, "get_candidate_profile", lambda *_a, **_k: profile)
    monkeypatch.setattr(
        career_companion,
        "build_companion_context",
        lambda *_a, **_k: SimpleNamespace(projects=[], vacancy_matches=[]),
    )

    captured: dict = {}
    vacancy_id = uuid4()

    def _plan(mode: str, target_role: str | None, target_vacancy_id):
        return SimpleNamespace(
            id=uuid4(),
            mode=mode,
            target_vacancy_id=target_vacancy_id,
            target_role=target_role,
            status="active",
            generation_mode="fallback",
            summary={"headline": "ok"},
            current_position={
                "goal_label": "x",
                "verified_skills": [],
                "missing_required_skills": [],
                "readiness": "not_ready",
                "strongest_projects": [],
            },
            actions=[],
            progress_events=[],
            chat_messages=[],
        )

    def _generate(*_a, **kwargs):
        captured.clear()
        captured.update(kwargs)
        return _plan(
            kwargs["mode"], kwargs.get("target_role"), kwargs.get("target_vacancy_id")
        )

    monkeypatch.setattr(career_companion, "generate_plan", _generate)

    cases = [
        ({"mode": "target_vacancy", "target_vacancy_id": str(vacancy_id), "target_role": None}, vacancy_id, None),
        ({"mode": "target_role", "target_vacancy_id": None, "target_role": "Backend Developer"}, None, "Backend Developer"),
        ({"mode": "career_growth", "target_vacancy_id": None, "target_role": None}, None, None),
        ({"mode": "explore_direction", "target_vacancy_id": None, "target_role": None}, None, None),
    ]

    for payload, expected_vacancy, expected_role in cases:
        monkeypatch.setattr(
            career_companion,
            "get_active_plan",
            lambda *_a, **_k: _plan(
                payload["mode"], expected_role, expected_vacancy
            ),
        )
        response = client.post(
            "/api/v1/candidate/career-companion/generate", json=payload
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["mode"] == payload["mode"]
        assert captured["mode"] == payload["mode"]
        assert captured["target_vacancy_id"] == expected_vacancy
        assert captured["target_role"] == expected_role
        CareerCompanionPlanResponse.model_validate(body)


def test_generate_rejects_unknown_mode(client: TestClient) -> None:
    authorize_candidate(make_user())
    response = client.post(
        "/api/v1/candidate/career-companion/generate",
        json={"mode": "explore_directions", "target_role": None},
    )
    assert response.status_code == 422


def test_generate_enqueue_failure_still_returns_plan(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import career_companion
    from types import SimpleNamespace

    user = make_user()
    profile = make_profile(user.id)
    authorize_candidate(user)
    monkeypatch.setattr(career_companion, "get_candidate_profile", lambda *_a, **_k: profile)

    plan = SimpleNamespace(
        id=uuid4(),
        mode="target_role",
        target_vacancy_id=None,
        target_role="Backend Developer",
        status="active",
        generation_mode="fallback",
        summary={"headline": "ok"},
        current_position={"goal_label": "Backend Developer", "verified_skills": [], "missing_required_skills": [], "readiness": "building", "strongest_projects": []},
        actions=[],
        progress_events=[],
        chat_messages=[],
    )
    monkeypatch.setattr(career_companion, "generate_plan", lambda *_a, **_k: plan)
    monkeypatch.setattr(
        career_companion,
        "build_companion_context",
        lambda *_a, **_k: SimpleNamespace(projects=[object()] * 8, vacancy_matches=[]),
    )
    monkeypatch.setattr(
        career_companion,
        "enqueue_async_regenerate_if_large",
        lambda **_k: (_ for _ in ()).throw(RuntimeError("enqueue boom")),
    )
    monkeypatch.setattr(career_companion, "get_active_plan", lambda *_a, **_k: plan)

    response = client.post(
        "/api/v1/candidate/career-companion/generate",
        json={"mode": "target_role", "target_role": "Backend Developer"},
    )
    assert response.status_code == 200
    CareerCompanionPlanResponse.model_validate(response.json())
