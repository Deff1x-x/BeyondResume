"""Deterministic local provider for AI Interview Questions."""

from __future__ import annotations

import json

from app.schemas.interview_questions import InterviewQuestionsResponse


class MockInterviewQuestionsProviderError(Exception):
    """The mock provider could not read the interview context."""


class MockInterviewQuestionsProvider:
    """Build schema-compatible questions using only prompt context."""

    provider_name = "mock"
    _input_marker = "\nINPUT:\n"

    def generate(self, prompt: str) -> str:
        _, marker, serialized_context = prompt.rpartition(self._input_marker)
        if not marker or not serialized_context.strip():
            raise MockInterviewQuestionsProviderError(
                "Prompt does not contain a valid INPUT section"
            )
        try:
            context = json.loads(serialized_context)
        except json.JSONDecodeError as error:
            raise MockInterviewQuestionsProviderError("Prompt INPUT is not valid JSON") from error
        if not isinstance(context, dict):
            raise MockInterviewQuestionsProviderError("Prompt INPUT must be a JSON object")

        facts = context.get("FACTS")
        gaps = context.get("GAPS")
        if not isinstance(facts, dict) or not isinstance(gaps, dict):
            raise MockInterviewQuestionsProviderError(
                "Prompt INPUT must contain FACTS and GAPS objects"
            )

        questions: list[dict[str, object]] = []

        missing_required = _string_list(gaps.get("missing_required_skills"))
        for skill in missing_required[:3]:
            questions.append(
                {
                    "category": "risk_validation",
                    "question": (
                        f"How have you applied {skill} in a recent role or project "
                        f"relevant to this vacancy?"
                    ),
                    "reason": (
                        f"{skill} is a required skill that is not yet confirmed in "
                        f"the candidate evidence for this vacancy."
                    ),
                    "target_skill": skill,
                    "evidence_basis": None,
                }
            )

        matched_required = _matched_skills(facts.get("matched_required_skills"))
        for item in matched_required[:3]:
            skill_name = item["name"]
            if skill_name is None:
                continue
            skill = skill_name
            evidence_title = item.get("evidence_title")
            if evidence_title:
                questions.append(
                    {
                        "category": "experience",
                        "question": (
                            f"Walk through the work behind {evidence_title} and the "
                            f"specific {skill} decisions you owned."
                        ),
                        "reason": (
                            f"The candidate has evidence linked to {skill}, so the "
                            f"interview can validate depth and ownership of that work."
                        ),
                        "target_skill": skill,
                        "evidence_basis": f"Evidence: {evidence_title}",
                    }
                )
            else:
                questions.append(
                    {
                        "category": "technical",
                        "question": (
                            f"Describe a concrete example where you used {skill} to "
                            f"solve a production problem."
                        ),
                        "reason": (
                            f"{skill} is a matched required skill and should be probed "
                            f"for practical depth."
                        ),
                        "target_skill": skill,
                        "evidence_basis": item.get("evidence_basis"),
                    }
                )

        if len(questions) < 6:
            matched_preferred = _matched_skills(facts.get("matched_preferred_skills"))
            for item in matched_preferred[:1]:
                skill_name = item["name"]
                if skill_name is None:
                    continue
                skill = skill_name
                questions.append(
                    {
                        "category": "technical",
                        "question": (
                            f"How would you apply {skill} to the day-to-day work for "
                            f"this vacancy?"
                        ),
                        "reason": (
                            f"{skill} is a matched preferred skill that can strengthen "
                            f"fit if the candidate can apply it concretely."
                        ),
                        "target_skill": skill,
                        "evidence_basis": item.get("evidence_basis"),
                    }
                )

        ownership_source = _first_evidence_title(facts)
        if ownership_source is not None:
            questions.append(
                {
                    "category": "ownership",
                    "question": (
                        f"In the work related to {ownership_source}, what decision "
                        f"did you personally own and what result did it produce?"
                    ),
                    "reason": (
                        "Existing evidence can support a concrete ownership question "
                        "about responsibility and outcomes."
                    ),
                    "target_skill": None,
                    "evidence_basis": f"Evidence: {ownership_source}",
                }
            )

        if not questions:
            vacancy_title = facts.get("vacancy_title")
            title = (
                vacancy_title
                if isinstance(vacancy_title, str) and vacancy_title.strip()
                else "this role"
            )
            questions = [
                {
                    "category": "experience",
                    "question": (
                        f"What recent work is most relevant to the responsibilities " f"of {title}?"
                    ),
                    "reason": (
                        "Limited candidate evidence is available, so the interview "
                        "should start with a concrete job-relevant experience probe."
                    ),
                    "target_skill": None,
                    "evidence_basis": None,
                },
                {
                    "category": "ownership",
                    "question": (
                        "Describe a delivery problem you personally drove to resolution "
                        "and what changed as a result."
                    ),
                    "reason": (
                        "Sparse evidence still allows a neutral ownership question about "
                        "observable work behavior."
                    ),
                    "target_skill": None,
                    "evidence_basis": None,
                },
            ]

        # Local schema validation only guarantees the transport payload shape;
        # semantic and safety validation stay in the service layer.
        return InterviewQuestionsResponse.model_validate(
            {"questions": questions[:8]}
        ).model_dump_json()


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            continue
        skill = item.strip()
        if not skill:
            continue
        identity = skill.casefold()
        if identity in seen:
            continue
        seen.add(identity)
        result.append(skill)
    return sorted(result, key=str.casefold)


def _matched_skills(value: object) -> list[dict[str, str | None]]:
    if not isinstance(value, list):
        return []
    result: list[dict[str, str | None]] = []
    for item in value:
        if isinstance(item, str):
            name = item.strip()
            if name:
                result.append({"name": name, "evidence_title": None, "evidence_basis": None})
            continue
        if not isinstance(item, dict):
            continue
        raw_name = item.get("name")
        if not isinstance(raw_name, str) or not raw_name.strip():
            continue
        evidence_title = item.get("evidence_title")
        evidence_basis = item.get("evidence_basis")
        result.append(
            {
                "name": raw_name.strip(),
                "evidence_title": (
                    evidence_title.strip()
                    if isinstance(evidence_title, str) and evidence_title.strip()
                    else None
                ),
                "evidence_basis": (
                    evidence_basis.strip()
                    if isinstance(evidence_basis, str) and evidence_basis.strip()
                    else None
                ),
            }
        )
    return sorted(result, key=lambda item: str(item["name"]).casefold())


def _first_evidence_title(facts: dict[str, object]) -> str | None:
    for key in ("matched_required_skills", "matched_preferred_skills"):
        for item in _matched_skills(facts.get(key)):
            title = item.get("evidence_title")
            if isinstance(title, str) and title.strip():
                return title.strip()
    evidence_summaries = facts.get("evidence_summaries")
    if isinstance(evidence_summaries, list):
        for item in evidence_summaries:
            if isinstance(item, dict):
                title = item.get("title")
                if isinstance(title, str) and title.strip():
                    return title.strip()
            elif isinstance(item, str) and item.strip():
                return item.strip()
    return None
