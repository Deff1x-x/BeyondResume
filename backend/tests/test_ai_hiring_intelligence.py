import json
from uuid import uuid4

import pytest

from app.schemas.skill_passport import SkillPassportEvidenceResponse, SkillPassportResponse, SkillPassportSkillResponse
from app.services import ai_hiring_intelligence as service
from app.services.ai_hiring_intelligence import HiringIntelligenceUnavailableError, build_hiring_context, get_hiring_intelligence


def passport(*skills: tuple[str, float]) -> SkillPassportResponse:
    return SkillPassportResponse(skills=[SkillPassportSkillResponse(id=uuid4(), name=name, category="language", evidence_confidence=confidence, evidence_count=1, evidence=[SkillPassportEvidenceResponse(id=uuid4(), title=None, description=None, source_type="github_repository", source_reference="repo", evidence_confidence=confidence)], github_repositories=[]) for name, confidence in skills], total_skills=len(skills), total_evidence=len(skills))


def test_context_is_deterministic_limited_and_has_no_raw_source_data() -> None:
    context = build_hiring_context(candidate_name="Private Name", passport=passport(*[(f"Skill{i:02d}", 0.5 + i / 100) for i in range(25)]))
    payload = context.as_payload()
    assert len(context.skills) == 20
    assert [item["name"] for item in context.skills] == sorted([item["name"] for item in context.skills], key=lambda name: next(-int(row["confidence"]) for row in context.skills if row["name"] == name))
    assert "Private Name" not in json.dumps(payload)
    assert "README" not in json.dumps(payload)
    assert "extracted_text" not in json.dumps(payload)
    assert context.as_payload() == context.as_payload()


def test_threshold_and_empty_context_are_backend_controlled() -> None:
    context = build_hiring_context(candidate_name=None, passport=passport(("Low", 0.49), ("Eligible", 0.50)))
    assert context.as_payload()["eligible_skills"] == ["Eligible"]
    empty = get_hiring_intelligence(build_hiring_context(candidate_name=None, passport=passport(("Low", 0.49))))
    assert empty.verdict.technical_interview_recommendation == "insufficient_evidence"
    assert empty.interview_questions == []


def test_valid_response_cache_and_semantic_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    service._cache.clear()
    context = build_hiring_context(candidate_name=None, passport=passport(("Python", 0.8)))
    provider = type("Provider", (), {"calls": 0, "generate": lambda self, _prompt: setattr(self, "calls", self.calls + 1) or json.dumps({"verdict": {"technical_interview_recommendation": "recommended", "confidence": 80, "summary": "Evidence supports a technical interview.", "strengths": ["Python evidence"], "concerns": []}, "interview_questions": [{"skill": "Python", "difficulty": "medium", "question": "Explain Python typing.", "reason": "Confirmed evidence."}]})})()
    monkeypatch.setattr(service.settings, "llm_provider", "openai")
    monkeypatch.setattr(service, "get_llm_provider", lambda: provider)
    assert get_hiring_intelligence(context).verdict.confidence == 80
    assert get_hiring_intelligence(context).verdict.confidence == 80
    assert provider.calls == 1
    service._cache.clear()
    provider.generate = lambda _prompt: json.dumps({"verdict": {"technical_interview_recommendation": "recommended", "confidence": 80, "summary": "ok", "strengths": [], "concerns": []}, "interview_questions": [{"skill": "Unknown", "difficulty": "medium", "question": "Q", "reason": "R"}]})
    with pytest.raises(HiringIntelligenceUnavailableError):
        get_hiring_intelligence(context)


@pytest.mark.parametrize("content", ["not json", "```json\n{\"verdict\": {}}\n```", ""])
def test_invalid_provider_content_is_not_cached(monkeypatch: pytest.MonkeyPatch, content: str) -> None:
    service._cache.clear()
    context = build_hiring_context(candidate_name=None, passport=passport(("Python", 0.8)))
    monkeypatch.setattr(service.settings, "llm_provider", "openai")
    monkeypatch.setattr(service, "get_llm_provider", lambda: type("P", (), {"generate": lambda *_: content})())
    with pytest.raises(HiringIntelligenceUnavailableError):
        get_hiring_intelligence(context)
    assert not service._cache.items
