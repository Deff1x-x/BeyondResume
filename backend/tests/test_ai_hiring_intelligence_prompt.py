import json

from app.prompts.ai_hiring_intelligence import (
    COMPLETE_EXAMPLE_JSON,
    INSUFFICIENT_EVIDENCE_EXAMPLE_JSON,
    RESPONSE_JSON_SCHEMA,
    SYSTEM_RULES,
)
from app.schemas.ai_hiring_intelligence import AiHiringIntelligenceResponse


def test_prompt_declares_the_complete_response_contract() -> None:
    assert "Return ONLY one valid JSON object" in SYSTEM_RULES
    assert "Do not omit fields" in SYSTEM_RULES
    assert "interview questions" in SYSTEM_RULES.lower()
    assert "Do NOT include" in SYSTEM_RULES or "do NOT include" in SYSTEM_RULES
    assert "executive_summary" in SYSTEM_RULES
    assert "hiring_risks" in SYSTEM_RULES
    assert "confidence_explanation" in SYSTEM_RULES
    assert "first_90_days_focus" in SYSTEM_RULES
    assert "recommended_next_action" in SYSTEM_RULES
    assert "interview_questions" not in RESPONSE_JSON_SCHEMA.get("properties", {})
    assert "questions" not in RESPONSE_JSON_SCHEMA.get("properties", {})
    assert RESPONSE_JSON_SCHEMA["title"] == "AiHiringIntelligenceResponse"
    complete = AiHiringIntelligenceResponse.model_validate(json.loads(COMPLETE_EXAMPLE_JSON))
    insufficient = AiHiringIntelligenceResponse.model_validate(
        json.loads(INSUFFICIENT_EVIDENCE_EXAMPLE_JSON)
    )
    assert complete.verdict == "hire"
    assert insufficient.verdict == "insufficient_evidence"
    assert "interview_questions" not in complete.model_dump()
    assert "concerns" not in complete.model_dump()
