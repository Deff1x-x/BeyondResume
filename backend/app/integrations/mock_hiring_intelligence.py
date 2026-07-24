"""Deterministic local provider for AI Hiring Intelligence."""

from __future__ import annotations

import json

from app.schemas.ai_hiring_intelligence import AiHiringIntelligenceResponse

_MAX_QUESTION_SKILL_LENGTH = 120


class MockHiringIntelligenceProviderError(Exception):
    """The mock provider could not read the hiring context."""


class MockHiringIntelligenceProvider:
    """Build a schema-compatible response using only prompt context."""

    provider_name = "mock"
    _input_marker = "\nINPUT:\n"

    def generate(self, prompt: str) -> str:
        # The serialized context is a single JSON line appended after the final
        # marker; json.dumps escapes newlines, so the last marker is the real one.
        _, marker, serialized_context = prompt.rpartition(self._input_marker)
        if not marker or not serialized_context.strip():
            raise MockHiringIntelligenceProviderError(
                "Prompt does not contain a valid INPUT section"
            )

        try:
            context = json.loads(serialized_context)
        except json.JSONDecodeError as error:
            raise MockHiringIntelligenceProviderError("Prompt INPUT is not valid JSON") from error

        if not isinstance(context, dict):
            raise MockHiringIntelligenceProviderError("Prompt INPUT must be a JSON object")

        raw_eligible_skills = context.get("eligible_skills")
        if not isinstance(raw_eligible_skills, list):
            raise MockHiringIntelligenceProviderError(
                "Prompt INPUT eligible_skills must be a JSON array"
            )

        eligible_skills: list[str] = []
        seen_skills: set[str] = set()
        for value in raw_eligible_skills:
            if not isinstance(value, str):
                raise MockHiringIntelligenceProviderError(
                    "Prompt INPUT contains a non-string eligible skill"
                )
            skill = value.strip()
            # Skip names the response schema cannot carry instead of failing.
            if not skill or len(skill) > _MAX_QUESTION_SKILL_LENGTH:
                continue
            identity = skill.casefold()
            if identity not in seen_skills:
                seen_skills.add(identity)
                eligible_skills.append(skill)

        payload: dict[str, object]
        if not eligible_skills:
            payload = {
                "verdict": {
                    "technical_interview_recommendation": "insufficient_evidence",
                    "confidence": 0,
                    "summary": (
                        "There is not enough eligible technical evidence to recommend "
                        "an interview."
                    ),
                    "strengths": [],
                    "concerns": ["No eligible skills are present in the supplied context."],
                },
                "interview_questions": [],
            }
        else:
            selected_skills = eligible_skills[:3]
            payload = {
                "verdict": {
                    "technical_interview_recommendation": "recommended",
                    "confidence": 75,
                    "summary": (
                        "The supplied technical evidence supports proceeding with "
                        "a focused interview."
                    ),
                    "strengths": [
                        f"Eligible evidence is available for {skill}." for skill in selected_skills
                    ],
                    "concerns": [],
                },
                "interview_questions": [
                    {
                        "skill": skill,
                        "difficulty": "medium",
                        "question": (
                            f"Describe a technically challenging use of {skill} "
                            "and explain your key design decisions."
                        ),
                        "reason": f"{skill} is an eligible skill in the supplied context.",
                    }
                    for skill in selected_skills
                ],
            }

        # Local schema validation only guarantees the transport payload shape;
        # semantic validation stays in the service layer.
        return AiHiringIntelligenceResponse.model_validate(payload).model_dump_json()
