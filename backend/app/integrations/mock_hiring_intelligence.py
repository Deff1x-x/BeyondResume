"""Deterministic local provider for AI Hiring Intelligence."""

from __future__ import annotations

import json

from app.schemas.ai_hiring_intelligence import AiHiringIntelligenceResponse

_MAX_SKILL_NAME_LENGTH = 120

_BACKEND_MARKERS = {"python", "fastapi", "postgresql", "docker", "redis", "kubernetes"}
_FRONTEND_MARKERS = {"react", "typescript", "next.js", "vue.js", "javascript", "css", "html"}
_INFRA_MARKERS = {"docker", "kubernetes", "linux", "nginx", "github actions"}


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

        payload = _build_payload(eligible_skills)
        # Local schema validation only guarantees the transport payload shape;
        # semantic validation stays in the service layer.
        return AiHiringIntelligenceResponse.model_validate(payload).model_dump_json()


def _normalized(skills: list[str]) -> set[str]:
    return {skill.casefold() for skill in skills}


def _build_payload(eligible_skills: list[str]) -> dict[str, object]:
    if not eligible_skills:
        return {
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

    names = _normalized(eligible_skills)
    backend_hits = len(names & _BACKEND_MARKERS)
    frontend_hits = len(names & _FRONTEND_MARKERS)
    has_fastapi = "fastapi" in names
    has_docker = "docker" in names
    has_postgres = "postgresql" in names
    selected = eligible_skills[:3]

    # Distinct archetypes from eligible skill mix (deterministic, context-driven).
    if has_fastapi and has_docker and has_postgres and backend_hits >= 3:
        return {
            "verdict": "strong_hire",
            "confidence": 84,
            "executive_summary": (
                "Backend depth looks strong across Python service and data-layer evidence. "
                "This profile is a credible platform hire if remaining preferred gaps are probed."
            ),
            "strengths": [
                f"Confirmed backend signal for {selected[0]}.",
                "Evidence suggests ownership of service and data-layer work.",
                *(
                    [f"Additional eligible coverage includes {selected[1]}."]
                    if len(selected) > 1
                    else []
                ),
            ][:5],
            "hiring_risks": [
                "Limited DevOps / orchestration evidence relative to a pure platform bar.",
            ],
            "confidence_explanation": [
                f"{skill} meets the evidence confidence threshold." for skill in selected[:2]
            ],
            "first_90_days_focus": [
                f"Validate production ownership stories around {selected[0]}.",
                "Probe operational maturity (deployments, observability, incident response).",
            ],
            "recommended_next_action": "Advance to a deep backend / system-design interview.",
        }

    if has_fastapi and frontend_hits >= 2:
        return {
            "verdict": "hire",
            "confidence": 72,
            "executive_summary": (
                "Versatile full-stack evidence spans frontend and backend skills. Useful for "
                "product delivery; less specialized than a dedicated platform profile."
            ),
            "strengths": [
                "Cross-stack versatility across eligible frontend and backend skills.",
                f"Eligible evidence includes {', '.join(selected[:2])}.",
            ],
            "hiring_risks": [
                "Backend specialization may be thinner than a platform-focused hire.",
                "Confirm depth on infrastructure requirements in interview.",
            ],
            "confidence_explanation": [
                f"{skill} contributes eligible evidence for this recommendation."
                for skill in selected[:2]
            ],
            "first_90_days_focus": [
                "Map which stack areas they owned end-to-end.",
                f"Pair with a senior owner on production {selected[0]} work.",
            ],
            "recommended_next_action": "Continue with a balanced full-stack technical screen.",
        }

    if has_postgres and not has_fastapi and not has_docker:
        lead = selected[0]
        return {
            "verdict": "consider",
            "confidence": 58,
            "executive_summary": (
                "Growth potential is visible, but eligible production evidence is still partial. "
                "Treat as a high-potential consider rather than a ready platform hire."
            ),
            "strengths": [
                f"Clear learning signal around {lead}.",
                "Project evidence suggests upward trajectory if mentorship is available.",
            ],
            "hiring_risks": [
                "Missing production depth on FastAPI and Docker.",
                "May need longer ramp time before independent ownership.",
            ],
            "confidence_explanation": [
                "Confidence is moderate because eligible coverage is still developing.",
                f"{lead} is eligible but should not be over-weighted alone.",
            ],
            "first_90_days_focus": [
                "Assign a scoped ownership project with explicit review checkpoints.",
                "Close the highest-priority skill gaps with paired delivery.",
            ],
            "recommended_next_action": "Keep in consideration; probe ramp plan and coaching needs.",
        }

    return {
        "verdict": "do_not_hire",
        "confidence": 46,
        "executive_summary": (
            "Transferable engineering skills are present, but too many role-critical gaps remain "
            "for a confident platform hire from the current evidence."
        ),
        "strengths": [
            f"Adjacent strengths include {', '.join(selected[:2])}.",
            "General engineering fundamentals may transfer with significant ramp.",
        ],
        "hiring_risks": [
            "Multiple required platform skills lack eligible evidence.",
            "Hiring now would rely on potential rather than demonstrated fit.",
        ],
        "confidence_explanation": [
            "Confidence stays limited because eligible skills do not cover the core role bar.",
        ],
        "first_90_days_focus": [
            "Only proceed if the hiring bar can flex toward a generalist ramp plan.",
        ],
        "recommended_next_action": "Deprioritize unless requirements are broadened.",
    }
