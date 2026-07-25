from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import require_employer
from app.db.session import get_db
from app.main import app
from app.models.user import User
from app.schemas.ai_hiring_intelligence import AiHiringIntelligenceResponse
from app.schemas.skill_passport import SkillPassportResponse, SkillPassportSkillResponse


@pytest.fixture
def client() -> TestClient:
    app.dependency_overrides[get_db] = lambda: SimpleNamespace()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_employer_ai_endpoint_returns_validated_response(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import employer

    employer_user = User(
        id=uuid4(),
        email="employer@example.com",
        password_hash="hash",
        role="employer",
        status="active",
    )
    candidate_id = uuid4()
    vacancy_id = uuid4()
    app.dependency_overrides[require_employer] = lambda: employer_user
    monkeypatch.setattr(employer, "_require_owned_vacancy", lambda *_args: SimpleNamespace())
    monkeypatch.setattr(
        employer, "build_match_details", lambda *_args, **_kwargs: SimpleNamespace()
    )
    monkeypatch.setattr(
        employer,
        "build_passport",
        lambda *_args: SkillPassportResponse(
            skills=[
                SkillPassportSkillResponse(
                    id=uuid4(),
                    name="Python",
                    category="language",
                    evidence_confidence=0.8,
                    evidence_count=1,
                    evidence=[],
                )
            ],
            total_skills=1,
            total_evidence=1,
        ),
    )
    monkeypatch.setattr(
        employer,
        "get_hiring_intelligence",
        lambda _context: AiHiringIntelligenceResponse.model_validate(
            {
                "verdict": "hire",
                "confidence": 80,
                "executive_summary": "The supplied evidence supports moving forward with this candidate.",
                "strengths": ["Verified Python evidence"],
                "hiring_risks": ["Limited Redis coverage"],
                "confidence_explanation": ["Python experience is supported by verified evidence"],
                "first_90_days_focus": ["Build familiarity with the existing service architecture"],
                "recommended_next_action": "Proceed to the next hiring stage.",
            }
        ),
    )

    response = client.get(
        f"/api/v1/employer/matches/{candidate_id}/ai-hiring-intelligence?vacancy_id={vacancy_id}"
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "verdict",
        "confidence",
        "executive_summary",
        "strengths",
        "hiring_risks",
        "confidence_explanation",
        "first_90_days_focus",
        "recommended_next_action",
    }
    assert body["verdict"] == "hire"
    assert body["confidence"] == 80
    assert body["executive_summary"]
    assert body["hiring_risks"] == ["Limited Redis coverage"]
    assert body["confidence_explanation"]
    assert body["first_90_days_focus"]
    assert body["recommended_next_action"]
    assert "interview_questions" not in body
    assert "questions" not in body
    assert "concerns" not in body
    assert "technical_interview_recommendation" not in body
    assert not isinstance(body["verdict"], dict)
