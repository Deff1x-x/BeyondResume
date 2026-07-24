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
    assert len(result.interview_questions) == 3
    assert len(result.interview_questions) <= 3
    assert {question.skill for question in result.interview_questions} <= {
        "Python",
        "FastAPI",
        "SQL",
        "Git",
    }
    identities = {
        (question.skill.casefold(), question.question.casefold())
        for question in result.interview_questions
    }
    assert len(identities) == len(result.interview_questions)
    assert len({question.skill.casefold() for question in result.interview_questions}) == len(
        result.interview_questions
    )


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

    assert result.verdict.technical_interview_recommendation == "insufficient_evidence"
    assert result.interview_questions == []


def test_mock_provider_ignores_blank_and_duplicate_skill_names() -> None:
    payload = json.dumps(
        {"eligible_skills": ["", "   ", "Python", " Python ", "python", "X" * 121, "Go"]}
    )
    content = MockHiringIntelligenceProvider().generate(f"rules\nINPUT:\n{payload}")
    result = AiHiringIntelligenceResponse.model_validate_json(content)

    assert [question.skill for question in result.interview_questions] == ["Python", "Go"]
