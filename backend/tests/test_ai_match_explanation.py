from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import require_employer
from app.db.session import get_db
from app.main import app
from app.models.user import User
from app.schemas.employer import (
    AiMatchExplanationResponse,
    MatchDetailsCandidateResponse,
    MatchDetailsEvidenceResponse,
    MatchDetailsMatchResponse,
    MatchDetailsPassportResponse,
    MatchDetailsResponse,
    MatchDetailsRoadmapItemResponse,
    MatchSkillGroupResponse,
)
from app.schemas.skill_passport import SkillPassportResponse, SkillPassportSkillResponse
from app.services.ai_match_explanation import (
    MatchExplanationUnavailableError,
    build_explanation_input,
    build_explanation_prompt,
    explain_match,
    parse_explanation_json,
)


def _details() -> MatchDetailsResponse:
    return MatchDetailsResponse(
        candidate=MatchDetailsCandidateResponse(id=uuid4(), name="Ada", headline=None, avatar=None),
        match=MatchDetailsMatchResponse(
            score=67,
            required=MatchSkillGroupResponse(matched=["Python"], missing=["C#"]),
            preferred=MatchSkillGroupResponse(matched=[], missing=["Redis"]),
        ),
        passport=MatchDetailsPassportResponse(top_skills=["Python", "FastAPI"]),
        evidence=[MatchDetailsEvidenceResponse(source_type="github_repository", title="Repository", skills=["Python"])],
        roadmap=[MatchDetailsRoadmapItemResponse(id="roadmap.vacancy_gap.csharp.v1", title="Build C# fundamentals", reason="Gap", priority="high", missing_skills=["C#"], related_skills=[])],
    )


def _input():
    return build_explanation_input(
        details=_details(),
        confirmed_skills=["Python", "FastAPI"],
        vacancy_title="Backend Engineer",
        required_skills=["Python", "C#"],
        preferred_skills=["Redis"],
    )


def test_prompt_builder_contains_only_prepared_match_input() -> None:
    prompt = build_explanation_prompt(_input())

    assert "Backend Engineer" in prompt
    assert "C#" in prompt
    assert "raw resume" not in prompt
    assert "Repository" not in prompt


def test_json_parser_rejects_invalid_response() -> None:
    with pytest.raises(MatchExplanationUnavailableError):
        parse_explanation_json("not json")


def test_explanation_cache_reuses_same_match_input(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services import ai_match_explanation

    ai_match_explanation._cache.clear()
    provider = Mock()
    provider.generate.return_value = '{"summary":"Match explanation.","strengths":["Python"],"gaps":["C#"],"next_steps":["Build C# fundamentals"]}'
    monkeypatch.setattr(ai_match_explanation, "get_llm_provider", lambda: provider)

    assert explain_match(_input()).summary == "Match explanation."
    assert explain_match(_input()).summary == "Match explanation."
    assert provider.generate.call_count == 1


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = lambda: Mock()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _employer() -> User:
    return User(id=uuid4(), email="employer@example.com", password_hash="hash", role="employer", status="active")


def test_explanation_endpoint_returns_structured_response(client, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.v1 import employer

    user = _employer()
    candidate_id = uuid4()
    vacancy_id = uuid4()
    app.dependency_overrides[require_employer] = lambda: user
    monkeypatch.setattr(employer, "_require_owned_vacancy", lambda *_args: SimpleNamespace(id=uuid4()))
    monkeypatch.setattr(employer, "get_vacancy", lambda *_args: SimpleNamespace(title="Backend Engineer"))
    monkeypatch.setattr(employer, "build_match_details", lambda *_args, **_kwargs: _details())
    monkeypatch.setattr(employer, "list_vacancy_requirements", lambda *_args: [])
    monkeypatch.setattr(employer, "build_passport", lambda *_args: SkillPassportResponse(skills=[SkillPassportSkillResponse(id=uuid4(), name="Python", category="language", evidence_confidence=1, evidence_count=1, evidence=[])], total_skills=1, total_evidence=1))
    monkeypatch.setattr(employer, "explain_match", lambda *_args: AiMatchExplanationResponse(summary="Explained.", strengths=["Python"], gaps=["C#"], next_steps=["Learn C#"]))

    response = client.post(f"/api/v1/employer/matches/{candidate_id}/explanation?vacancy_id={vacancy_id}")

    assert response.status_code == 200
    assert response.json()["summary"] == "Explained."


def test_explanation_endpoint_falls_back_when_llm_is_unavailable(client, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.v1 import employer

    user = _employer()
    candidate_id = uuid4()
    vacancy_id = uuid4()
    app.dependency_overrides[require_employer] = lambda: user
    monkeypatch.setattr(employer, "_require_owned_vacancy", lambda *_args: SimpleNamespace(id=uuid4()))
    monkeypatch.setattr(employer, "get_vacancy", lambda *_args: SimpleNamespace(title="Backend Engineer"))
    monkeypatch.setattr(employer, "build_match_details", lambda *_args, **_kwargs: _details())
    monkeypatch.setattr(employer, "list_vacancy_requirements", lambda *_args: [])
    monkeypatch.setattr(employer, "build_passport", lambda *_args: SkillPassportResponse(skills=[], total_skills=0, total_evidence=0))
    monkeypatch.setattr(employer, "explain_match", lambda *_args: (_ for _ in ()).throw(MatchExplanationUnavailableError()))

    response = client.post(f"/api/v1/employer/matches/{candidate_id}/explanation?vacancy_id={vacancy_id}")

    assert response.status_code == 503
    assert response.json()["error"]["message"] == "AI explanation is currently unavailable."
