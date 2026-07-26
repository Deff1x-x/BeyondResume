"""Deterministic local provider for AI Hiring Intelligence."""

from __future__ import annotations

import json

from app.schemas.ai_hiring_intelligence import AiHiringIntelligenceResponse

_MAX_SKILL_NAME_LENGTH = 120


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
            if not skill or len(skill) > _MAX_SKILL_NAME_LENGTH:
                continue
            identity = skill.casefold()
            if identity not in seen_skills:
                seen_skills.add(identity)
                eligible_skills.append(skill)

        payload: dict[str, object]
        if not eligible_skills:
            payload = {
                "verdict": "insufficient_evidence",
                "confidence": 0,
                "executive_summary": (
                    "There is not enough eligible technical evidence to form a hiring "
                    "recommendation."
                ),
                "strengths": [],
                "hiring_risks": ["No eligible skills are present in the supplied context."],
                "confidence_explanation": [
                    "Confidence is low because no skills meet the evidence threshold."
                ],
                "first_90_days_focus": [],
                "recommended_next_action": (
                    "Request stronger verified technical evidence before proceeding."
                ),
            }
        else:
            selected_skills = eligible_skills[:3]
            focus_skills = selected_skills[:2]
            if len(eligible_skills) == 1:
                verdict = "consider"
                confidence = 55
                executive_summary = (
                    "Limited eligible technical evidence is available. Keep the candidate "
                    "in consideration while gathering stronger confirmation."
                )
                recommended_next_action = (
                    "Keep the candidate in consideration while reviewing alternatives."
                )
            else:
                verdict = "hire"
                confidence = 75
                executive_summary = (
                    "The supplied technical evidence supports moving forward with this "
                    "candidate based on confirmed eligible skills."
                )
                recommended_next_action = "Proceed to the next hiring stage."
            payload = {
                "verdict": verdict,
                "confidence": confidence,
                "executive_summary": executive_summary,
                "strengths": [
                    f"Eligible evidence is available for {skill}." for skill in selected_skills
                ],
                "hiring_risks": (
                    []
                    if len(eligible_skills) > 1
                    else ["Evidence coverage is limited to a single eligible skill."]
                ),
                "confidence_explanation": [
                    f"{skill} meets the evidence confidence threshold for a hiring recommendation."
                    for skill in focus_skills
                ],
                "first_90_days_focus": [
                    f"Build familiarity with day-to-day use of {skill} on the team."
                    for skill in focus_skills
                ],
                "recommended_next_action": recommended_next_action,
            }

        # Local schema validation only guarantees the transport payload shape;
        # semantic validation stays in the service layer.
        return AiHiringIntelligenceResponse.model_validate(payload).model_dump_json()
