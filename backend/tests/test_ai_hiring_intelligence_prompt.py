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
    assert "Do not replace nested objects with strings" in SYSTEM_RULES
    assert "Every interview_questions" in SYSTEM_RULES
    assert RESPONSE_JSON_SCHEMA["title"] == "AiHiringIntelligenceResponse"
    assert AiHiringIntelligenceResponse.model_validate(json.loads(COMPLETE_EXAMPLE_JSON))
    assert AiHiringIntelligenceResponse.model_validate(json.loads(INSUFFICIENT_EVIDENCE_EXAMPLE_JSON))
