import json

import pytest

from app.integrations.mock_hiring_intelligence import (
    MockHiringIntelligenceProvider,
    MockHiringIntelligenceProviderError,
)
from app.schemas.ai_hiring_intelligence import AiHiringIntelligenceResponse
from app.services.ai_hiring_intelligence import CandidateHiringContext, build_hiring_prompt


def _prompt(*skills: tuple[str, int]) -> str:
    context = CandidateHiringContext(
        skills=tuple(
            {
                "name": name,
                "confidence": confidence,
                "evidence_count": 1,
                "github_repositories": [],
                "sources": ["github_repository"],
            }
            for name, confidence in skills
        ),
        evidence_sources=("github_repository",),
    )
    return build_hiring_prompt(context)


def test_mock_provider_returns_deterministic_schema_valid_json() -> None:
    provider = MockHiringIntelligenceProvider()
    prompt = _prompt(("Python", 90), ("FastAPI", 80), ("SQL", 70), ("Git", 60))

    first = provider.generate(prompt)
    second = provider.generate(prompt)
    result = AiHiringIntelligenceResponse.model_validate_json(first)

    assert first == second
    assert json.loads(first)
    assert result.verdict == "hire"
    assert result.confidence == 75
    assert result.executive_summary
    assert len(result.strengths) == 3
    assert result.hiring_risks == []
    assert result.confidence_explanation
    assert result.first_90_days_focus
    assert result.recommended_next_action == "Proceed to the next hiring stage."
    dumped = result.model_dump()
    assert set(dumped) == {
        "verdict",
        "confidence",
        "executive_summary",
        "strengths",
        "hiring_risks",
        "confidence_explanation",
        "first_90_days_focus",
        "recommended_next_action",
    }
    assert "interview_questions" not in dumped
    assert "questions" not in dumped
    assert "concerns" not in dumped
    serialized = json.dumps(dumped).lower()
    assert "interview" not in serialized
    assert "question" not in serialized


def test_mock_provider_uses_consider_for_single_eligible_skill() -> None:
    content = MockHiringIntelligenceProvider().generate(_prompt(("Python", 90)))
    result = AiHiringIntelligenceResponse.model_validate_json(content)

    assert result.verdict == "consider"
    assert result.confidence == 55
    assert result.hiring_risks
    assert "consideration" in result.recommended_next_action.lower()
    assert "proceed to the next hiring stage" not in result.recommended_next_action.lower()


@pytest.mark.parametrize(
    "prompt",
    [
        "missing input marker",
        "\nINPUT:\nnot-json",
        "\nINPUT:\n[]",
        '\nINPUT:\n{"eligible_skills": "Python"}',
        '\nINPUT:\n{"eligible_skills": [42]}',
    ],
)
def test_mock_provider_rejects_malformed_prompt(prompt: str) -> None:
    with pytest.raises(MockHiringIntelligenceProviderError):
        MockHiringIntelligenceProvider().generate(prompt)


def test_mock_provider_handles_empty_eligible_skills() -> None:
    content = MockHiringIntelligenceProvider().generate(_prompt(("Unconfirmed", 49)))
    result = AiHiringIntelligenceResponse.model_validate_json(content)

    assert result.verdict == "insufficient_evidence"
    assert result.confidence == 0
    assert result.strengths == []
    assert result.hiring_risks
    assert result.first_90_days_focus == []
    assert "interview_questions" not in result.model_dump()


def test_mock_provider_ignores_blank_and_duplicate_skill_names() -> None:
    payload = json.dumps(
        {"eligible_skills": ["", "   ", "Python", " Python ", "python", "X" * 121, "Go"]}
    )
    content = MockHiringIntelligenceProvider().generate(f"rules\nINPUT:\n{payload}")
    result = AiHiringIntelligenceResponse.model_validate_json(content)

    assert [item for item in result.strengths if "Python" in item or "Go" in item] == [
        "Eligible evidence is available for Python.",
        "Eligible evidence is available for Go.",
    ]
