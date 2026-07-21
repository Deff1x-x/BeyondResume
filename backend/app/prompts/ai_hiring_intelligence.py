"""Prompt contract for the Evidence Engine interpretation layer."""

from __future__ import annotations

import json

from app.schemas.ai_hiring_intelligence import AiHiringIntelligenceResponse


PROMPT_VERSION = "ai-hiring-intelligence-v2"

# This is generated from the DTO used for final validation and is also supplied
# to OpenAI Structured Outputs by the provider.
RESPONSE_JSON_SCHEMA = AiHiringIntelligenceResponse.model_json_schema()


def _example_json(*, insufficient_evidence: bool) -> str:
    """Examples are serialized through the DTO so they cannot drift from it."""
    payload = (
        {
            "verdict": {
                "technical_interview_recommendation": "insufficient_evidence",
                "confidence": 25,
                "summary": "The supplied evidence is insufficient for a technical interview recommendation.",
                "strengths": [],
                "concerns": ["Insufficient verified technical evidence is available."],
            },
            "interview_questions": [],
        }
        if insufficient_evidence
        else {
            "verdict": {
                "technical_interview_recommendation": "recommended",
                "confidence": 87,
                "summary": "The supplied evidence supports a technical interview.",
                "strengths": ["Verified Python evidence", "Multiple evidence sources"],
                "concerns": ["Some relevant skills have limited coverage"],
            },
            "interview_questions": [
                {
                    "skill": "Python",
                    "difficulty": "medium",
                    "question": "Explain how you would structure error handling in a Python service.",
                    "reason": "Python is an eligible skill in the supplied evidence.",
                }
            ],
        }
    )
    return AiHiringIntelligenceResponse.model_validate(payload).model_dump_json(indent=2)


COMPLETE_EXAMPLE_JSON = _example_json(insufficient_evidence=False)
INSUFFICIENT_EVIDENCE_EXAMPLE_JSON = _example_json(insufficient_evidence=True)

SYSTEM_RULES = f"""You interpret only the supplied technical evidence summary.

Return ONLY one valid JSON object matching the response contract below.
Do not return Markdown, explanations, prose outside JSON, or code fences.
Do not omit fields. Do not add fields. Do not replace nested objects with strings.
Do not replace arrays of objects with arrays of strings.

The verdict value must be an object, never a string. Every interview_questions
element must be an object, never a string. The authoritative JSON Schema below
defines all required fields, allowed values, types, and limits.
Interview questions may target only skills in eligible_skills. Keep questions
technical and evidence-grounded.

Complete valid example:
{COMPLETE_EXAMPLE_JSON}

When evidence is insufficient, return the same schema, for example:
{INSUFFICIENT_EVIDENCE_EXAMPLE_JSON}

Full JSON Schema (authoritative):
{json.dumps(RESPONSE_JSON_SCHEMA, ensure_ascii=False, sort_keys=True)}

Do not inspect or request source code, README files, PDFs, resumes, repository
contents, or external data. Do not infer seniority, employment history,
personality, age, gender, nationality, or any protected trait. Do not invent
skills or facts. The recommendation is only an evidence-based indication of
whether a technical interview is worthwhile; it is not a hiring decision."""
