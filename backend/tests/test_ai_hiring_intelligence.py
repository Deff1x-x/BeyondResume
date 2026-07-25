import json
from uuid import uuid4

import pytest

from app.schemas.ai_hiring_intelligence import AiHiringIntelligenceResponse
from app.schemas.skill_passport import (
    SkillPassportEvidenceResponse,
    SkillPassportResponse,
    SkillPassportSkillResponse,
)
from app.services import ai_hiring_intelligence as service
from app.services.ai_hiring_intelligence import (
    HiringIntelligenceUnavailableError,
    build_hiring_context,
    get_hiring_intelligence,
)


def passport(*skills: tuple[str, float]) -> SkillPassportResponse:
    return SkillPassportResponse(
        skills=[
            SkillPassportSkillResponse(
                id=uuid4(),
                name=name,
                category="language",
                evidence_confidence=confidence,
                evidence_count=1,
                evidence=[
                    SkillPassportEvidenceResponse(
                        id=uuid4(),
                        title=None,
                        description=None,
                        source_type="github_repository",
                        source_reference="repo",
                        verification_status=None,
                        ownership_status=None,
                        evidence_confidence=confidence,
                    )
                ],
                github_repositories=[],
            )
            for name, confidence in skills
        ],
        total_skills=len(skills),
        total_evidence=len(skills),
    )


def _valid_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "verdict": "hire",
        "confidence": 80,
        "executive_summary": "The supplied evidence supports moving forward with this candidate.",
        "strengths": ["Python evidence"],
        "hiring_risks": [],
        "confidence_explanation": ["Python meets the evidence confidence threshold."],
        "first_90_days_focus": ["Build familiarity with the existing service architecture"],
        "recommended_next_action": "Proceed to the next hiring stage.",
    }
    payload.update(overrides)
    return payload


def test_context_is_deterministic_limited_and_has_no_raw_source_data() -> None:
    context = build_hiring_context(
        candidate_name="Private Name",
        passport=passport(*[(f"Skill{i:02d}", 0.5 + i / 100) for i in range(25)]),
    )
    payload = context.as_payload()
    assert len(context.skills) == 20
    assert [item["name"] for item in context.skills] == sorted(
        [item["name"] for item in context.skills],
        key=lambda name: next(
            -int(row["confidence"]) for row in context.skills if row["name"] == name
        ),
    )
    assert "Private Name" not in json.dumps(payload)
    assert "README" not in json.dumps(payload)
    assert "extracted_text" not in json.dumps(payload)
    assert context.as_payload() == context.as_payload()


def test_threshold_and_empty_context_are_backend_controlled() -> None:
    context = build_hiring_context(
        candidate_name=None, passport=passport(("Low", 0.49), ("Eligible", 0.50))
    )
    assert context.as_payload()["eligible_skills"] == ["Eligible"]
    empty = get_hiring_intelligence(
        build_hiring_context(candidate_name=None, passport=passport(("Low", 0.49)))
    )
    assert empty.verdict == "insufficient_evidence"
    assert empty.confidence == 0
    assert empty.hiring_risks
    dumped = empty.model_dump()
    assert "interview_questions" not in dumped
    assert "questions" not in dumped
    assert "concerns" not in dumped
    assert "executive_summary" in dumped
    assert "hiring_risks" in dumped
    assert "confidence_explanation" in dumped
    assert "first_90_days_focus" in dumped
    assert "recommended_next_action" in dumped


def test_valid_response_cache_and_semantic_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    service._cache.clear()
    context = build_hiring_context(candidate_name=None, passport=passport(("Python", 0.8)))
    provider = type(
        "Provider",
        (),
        {
            "calls": 0,
            "generate": lambda self, _prompt: setattr(self, "calls", self.calls + 1)
            or json.dumps(_valid_payload()),
        },
    )()
    monkeypatch.setattr(service, "get_hiring_intelligence_provider", lambda: provider)
    first = get_hiring_intelligence(context)
    second = get_hiring_intelligence(context)
    assert first.confidence == 80
    assert second.confidence == 80
    assert first.verdict == "hire"
    assert first.executive_summary
    assert provider.calls == 1
    dumped = first.model_dump()
    assert "interview_questions" not in dumped
    assert "questions" not in dumped
    assert "concerns" not in dumped

    service._cache.clear()
    provider.generate = lambda _prompt: json.dumps(
        _valid_payload(strengths=["", "Python evidence"])
    )
    with pytest.raises(HiringIntelligenceUnavailableError):
        get_hiring_intelligence(context)
    assert not service._cache.items


def test_missing_required_field_fails_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    service._cache.clear()
    context = build_hiring_context(candidate_name=None, passport=passport(("Python", 0.8)))
    incomplete = _valid_payload()
    del incomplete["recommended_next_action"]
    monkeypatch.setattr(
        service,
        "get_hiring_intelligence_provider",
        lambda: type("P", (), {"generate": lambda *_: json.dumps(incomplete)})(),
    )
    with pytest.raises(HiringIntelligenceUnavailableError):
        get_hiring_intelligence(context)
    assert not service._cache.items


def test_schema_rejects_interview_questions_field() -> None:
    payload = _valid_payload(interview_questions=[{"skill": "Python", "question": "Q"}])
    with pytest.raises(Exception):
        AiHiringIntelligenceResponse.model_validate(payload)


def test_schema_rejects_old_nested_verdict_shape() -> None:
    with pytest.raises(Exception):
        AiHiringIntelligenceResponse.model_validate(
            {
                "verdict": {
                    "technical_interview_recommendation": "recommended",
                    "confidence": 80,
                    "summary": "old",
                    "strengths": [],
                    "concerns": [],
                },
                "interview_questions": [],
            }
        )


@pytest.mark.parametrize("confidence", [-1, 101])
def test_schema_rejects_out_of_range_confidence(confidence: int) -> None:
    with pytest.raises(Exception):
        AiHiringIntelligenceResponse.model_validate(_valid_payload(confidence=confidence))


@pytest.mark.parametrize("confidence", [0, 100])
def test_schema_accepts_confidence_bounds(confidence: int) -> None:
    result = AiHiringIntelligenceResponse.model_validate(_valid_payload(confidence=confidence))
    assert result.confidence == confidence


def test_schema_rejects_invalid_verdict() -> None:
    with pytest.raises(Exception):
        AiHiringIntelligenceResponse.model_validate(_valid_payload(verdict="maybe"))


def test_schema_rejects_whitespace_only_required_strings() -> None:
    with pytest.raises(Exception):
        AiHiringIntelligenceResponse.model_validate(
            _valid_payload(executive_summary="   ", recommended_next_action="   ")
        )


def test_schema_exact_top_level_keys() -> None:
    result = AiHiringIntelligenceResponse.model_validate(_valid_payload())
    assert set(result.model_dump()) == {
        "verdict",
        "confidence",
        "executive_summary",
        "strengths",
        "hiring_risks",
        "confidence_explanation",
        "first_90_days_focus",
        "recommended_next_action",
    }


def test_cache_identity_includes_response_schema_version(monkeypatch: pytest.MonkeyPatch) -> None:
    service._cache.clear()
    context = build_hiring_context(candidate_name=None, passport=passport(("Python", 0.8)))
    provider = type(
        "Provider",
        (),
        {
            "calls": 0,
            "generate": lambda self, _prompt: setattr(self, "calls", self.calls + 1)
            or json.dumps(_valid_payload()),
        },
    )()
    monkeypatch.setattr(service, "get_hiring_intelligence_provider", lambda: provider)
    get_hiring_intelligence(context)
    get_hiring_intelligence(context)
    assert provider.calls == 1
    monkeypatch.setattr(service, "RESPONSE_SCHEMA_VERSION", "ai-hiring-response-test-version")
    get_hiring_intelligence(context)
    assert provider.calls == 2


def test_service_rejects_old_nested_provider_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    service._cache.clear()
    context = build_hiring_context(candidate_name=None, passport=passport(("Python", 0.8)))
    old_payload = {
        "verdict": {
            "technical_interview_recommendation": "recommended",
            "confidence": 80,
            "summary": "Evidence supports a technical interview.",
            "strengths": [],
            "concerns": [],
        },
        "interview_questions": [],
    }
    monkeypatch.setattr(
        service,
        "get_hiring_intelligence_provider",
        lambda: type("P", (), {"generate": lambda *_: json.dumps(old_payload)})(),
    )
    with pytest.raises(HiringIntelligenceUnavailableError):
        get_hiring_intelligence(context)
    assert not service._cache.items


def test_cache_identity_uses_provider_and_model(monkeypatch: pytest.MonkeyPatch) -> None:
    service._cache.clear()
    context = build_hiring_context(candidate_name=None, passport=passport(("Python", 0.8)))
    provider = type(
        "Provider",
        (),
        {
            "calls": 0,
            "generate": lambda self, _prompt: setattr(self, "calls", self.calls + 1)
            or json.dumps(_valid_payload()),
        },
    )()
    monkeypatch.setattr(service, "get_hiring_intelligence_provider", lambda: provider)
    monkeypatch.setattr(service.settings, "llm_provider", "mock")
    monkeypatch.setattr(service.settings, "llm_model", "model-a")
    get_hiring_intelligence(context)
    get_hiring_intelligence(context)
    assert provider.calls == 1
    monkeypatch.setattr(service.settings, "llm_model", "model-b")
    get_hiring_intelligence(context)
    assert provider.calls == 2
    monkeypatch.setattr(service.settings, "llm_provider", "openai")
    get_hiring_intelligence(context)
    get_hiring_intelligence(context)
    assert provider.calls == 3


@pytest.mark.parametrize("content", ["not json", '```json\n{"verdict": {}}\n```', ""])
def test_invalid_provider_content_is_not_cached(
    monkeypatch: pytest.MonkeyPatch, content: str
) -> None:
    service._cache.clear()
    context = build_hiring_context(candidate_name=None, passport=passport(("Python", 0.8)))
    monkeypatch.setattr(
        service,
        "get_hiring_intelligence_provider",
        lambda: type("P", (), {"generate": lambda *_: content})(),
    )
    with pytest.raises(HiringIntelligenceUnavailableError):
        get_hiring_intelligence(context)
    assert not service._cache.items
