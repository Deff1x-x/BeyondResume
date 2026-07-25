"""Prompt contract for the Evidence Engine hiring-decision layer."""

from __future__ import annotations

import json

from app.schemas.ai_hiring_intelligence import AiHiringIntelligenceResponse


PROMPT_VERSION = "ai-hiring-intelligence-v3"

# This is generated from the DTO used for final validation and is also supplied
# to OpenAI Structured Outputs by the provider.
RESPONSE_JSON_SCHEMA = AiHiringIntelligenceResponse.model_json_schema()


def _example_json(*, insufficient_evidence: bool) -> str:
    """Examples are serialized through the DTO so they cannot drift from it."""
    payload = (
        {
            "verdict": "insufficient_evidence",
            "confidence": 25,
            "executive_summary": (
                "The supplied evidence is insufficient to support a hiring decision."
            ),
            "strengths": [],
            "hiring_risks": ["Insufficient verified technical evidence is available."],
            "confidence_explanation": [
                "Confidence is low because no skills meet the evidence threshold."
            ],
            "first_90_days_focus": [],
            "recommended_next_action": (
                "Request stronger verified technical evidence before proceeding."
            ),
        }
        if insufficient_evidence
        else {
            "verdict": "hire",
            "confidence": 87,
            "executive_summary": (
                "The supplied evidence supports moving forward with this candidate."
            ),
            "strengths": ["Verified Python evidence", "Multiple evidence sources"],
            "hiring_risks": ["Some relevant skills have limited coverage"],
            "confidence_explanation": [
                "Python experience is supported by multiple evidence sources",
                "Cloud experience is present but less strongly demonstrated",
            ],
            "first_90_days_focus": [
                "Build familiarity with the existing service architecture",
                "Strengthen ownership of production testing practices",
            ],
            "recommended_next_action": "Proceed to the next hiring stage",
        }
    )
    return AiHiringIntelligenceResponse.model_validate(payload).model_dump_json(indent=2)


COMPLETE_EXAMPLE_JSON = _example_json(insufficient_evidence=False)
INSUFFICIENT_EVIDENCE_EXAMPLE_JSON = _example_json(insufficient_evidence=True)

SYSTEM_RULES = f"""You interpret only the supplied technical evidence summary.

Return ONLY one valid JSON object matching the response contract below.
Do not return Markdown, explanations, prose outside JSON, or code fences.
Do not omit fields. Do not add fields.

Produce an executive hiring decision for a hiring manager. Answer whether the
employer should move forward with this candidate, why, and what the main hiring
risks are.

Required fields:
- verdict: one of strong_hire, hire, consider, insufficient_evidence, do_not_hire
- confidence: integer from 0 to 100
- executive_summary: concise hiring-decision rationale grounded in evidence
- strengths: evidence-backed strengths (array of strings)
- hiring_risks: concrete hiring risks tied to missing, weak, or unverified evidence
- confidence_explanation: short user-facing evidence-based reasons for the
  confidence level (not internal reasoning or chain-of-thought)
- first_90_days_focus: potential onboarding priorities if hired (conditional;
  do not assert that hiring has occurred)
- recommended_next_action: one concise next step for the hiring manager;
  must be consistent with verdict, hiring_risks, and confidence

Explicitly do NOT include:
- interview questions
- interview plans
- interview preparation
- questions to ask
- interview focus areas
- unsupported factual claims
- protected or sensitive attribute inference
- salary estimation
- culture-fit assumptions
- personality diagnosis
- chain-of-thought or internal reasoning

Do not invent skills or facts that are absent from the supplied evidence.
Do not assert that the candidate will be hired.
first_90_days_focus describes potential onboarding priorities only.
recommended_next_action must align with verdict, hiring_risks, and confidence.

Complete valid example:
{COMPLETE_EXAMPLE_JSON}

When evidence is insufficient, return the same schema, for example:
{INSUFFICIENT_EVIDENCE_EXAMPLE_JSON}

Full JSON Schema (authoritative):
{json.dumps(RESPONSE_JSON_SCHEMA, ensure_ascii=False, sort_keys=True)}

Do not inspect or request source code, README files, PDFs, resumes, repository
contents, or external data. Do not infer seniority, employment history,
personality, age, gender, nationality, or any protected trait."""
