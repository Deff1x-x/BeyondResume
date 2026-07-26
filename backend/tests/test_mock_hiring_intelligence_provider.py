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


def test_mock_provider_returns_strong_hire_for_platform_backend_mix() -> None:
    provider = MockHiringIntelligenceProvider()
    prompt = _prompt(
        ("Python", 90),
        ("FastAPI", 88),
        ("PostgreSQL", 85),
        ("Docker", 80),
        ("Redis", 70),
    )

    first = provider.generate(prompt)
    second = provider.generate(prompt)
    result = AiHiringIntelligenceResponse.model_validate_json(first)

    assert first == second
    assert json.loads(first)
    assert result.verdict == "strong_hire"
    assert result.confidence == 84
    assert result.executive_summary
    assert result.strengths
    assert result.hiring_risks
    assert result.recommended_next_action


def test_mock_provider_returns_hire_for_fullstack_mix() -> None:
    content = MockHiringIntelligenceProvider().generate(
        _prompt(
            ("Python", 88),
            ("FastAPI", 80),
            ("TypeScript", 82),
            ("React", 79),
            ("PostgreSQL", 70),
        )
    )
    result = AiHiringIntelligenceResponse.model_validate_json(content)
    assert result.verdict == "hire"
    assert result.confidence == 72
    assert "versatile" in result.executive_summary.lower() or "full-stack" in result.executive_summary.lower()


def test_mock_provider_returns_consider_for_partial_backend() -> None:
    content = MockHiringIntelligenceProvider().generate(
        _prompt(("Python", 90), ("PostgreSQL", 80), ("TypeScript", 70), ("React", 68))
    )
    result = AiHiringIntelligenceResponse.model_validate_json(content)
    assert result.verdict == "consider"
    assert result.confidence == 58


def test_mock_provider_returns_do_not_hire_for_adjacent_profile() -> None:
    content = MockHiringIntelligenceProvider().generate(
        _prompt(("Python", 80), ("TypeScript", 75), ("React", 70), ("Go", 72), ("Linux", 65))
    )
    result = AiHiringIntelligenceResponse.model_validate_json(content)
    assert result.verdict == "do_not_hire"
    assert result.confidence == 46


def test_mock_provider_archetypes_are_not_identical() -> None:
    backend = AiHiringIntelligenceResponse.model_validate_json(
        MockHiringIntelligenceProvider().generate(
            _prompt(("Python", 90), ("FastAPI", 88), ("PostgreSQL", 85), ("Docker", 80))
        )
    )
    adjacent = AiHiringIntelligenceResponse.model_validate_json(
        MockHiringIntelligenceProvider().generate(
            _prompt(("Python", 80), ("TypeScript", 75), ("React", 70), ("Go", 72))
        )
    )
    assert backend.verdict != adjacent.verdict
    assert backend.executive_summary != adjacent.executive_summary
    assert backend.recommended_next_action != adjacent.recommended_next_action


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


def test_mock_provider_ignores_blank_and_duplicate_skill_names() -> None:
    payload = json.dumps(
        {"eligible_skills": ["", "   ", "Python", " Python ", "python", "X" * 121, "Go"]}
    )
    content = MockHiringIntelligenceProvider().generate(f"rules\nINPUT:\n{payload}")
    result = AiHiringIntelligenceResponse.model_validate_json(content)

    assert result.verdict == "do_not_hire"
    joined = " ".join(result.strengths)
    assert "Python" in joined or "Go" in joined
