"""Deterministic local provider for AI Candidate Compare."""

from __future__ import annotations

import json
from uuid import UUID

from app.schemas.ai_candidate_compare import AiCandidateCompareLlmPayload


class MockAiCandidateCompareProviderError(Exception):
    """The mock provider could not read the compare context."""


class MockAiCandidateCompareProvider:
    """Build a schema-compatible grounded response using only prompt INPUT."""

    provider_name = "mock"
    _input_marker = "\nINPUT:\n"

    def generate(self, prompt: str) -> str:
        _, marker, serialized_context = prompt.rpartition(self._input_marker)
        if not marker or not serialized_context.strip():
            raise MockAiCandidateCompareProviderError(
                "Prompt does not contain a valid INPUT section"
            )
        try:
            context = json.loads(serialized_context)
        except json.JSONDecodeError as error:
            raise MockAiCandidateCompareProviderError("Prompt INPUT is not valid JSON") from error
        if not isinstance(context, dict):
            raise MockAiCandidateCompareProviderError("Prompt INPUT must be a JSON object")

        candidates = context.get("candidates")
        facts = context.get("facts")
        if not isinstance(candidates, list) or len(candidates) < 2:
            raise MockAiCandidateCompareProviderError("Prompt INPUT candidates are invalid")
        if not isinstance(facts, dict):
            raise MockAiCandidateCompareProviderError("Prompt INPUT facts must be an object")

        fact_ids = {str(key) for key in facts}
        assessments: list[dict[str, object]] = []
        ordered_ids: list[str] = []
        for item in candidates:
            if not isinstance(item, dict):
                raise MockAiCandidateCompareProviderError("Candidate entry must be an object")
            candidate_id = item.get("candidate_id")
            if not isinstance(candidate_id, str):
                raise MockAiCandidateCompareProviderError("candidate_id must be a string")
            UUID(candidate_id)  # validate shape
            ordered_ids.append(candidate_id)
            match = item.get("match")
            if not isinstance(match, dict):
                raise MockAiCandidateCompareProviderError("match must be an object")
            matched_required = match.get("required_matched")
            missing_required = match.get("required_missing")
            if not isinstance(matched_required, list) or not isinstance(missing_required, list):
                raise MockAiCandidateCompareProviderError("match skill lists must be arrays")

            strengths: list[dict[str, object]] = []
            for skill in matched_required[:2]:
                if not isinstance(skill, str) or not skill.strip():
                    continue
                fact_id = f"candidate:{candidate_id}:matched-required:{_skill_token(skill)}"
                if fact_id in fact_ids:
                    strengths.append(
                        {
                            "text": f"Matches required skill {skill.strip()} in system facts.",
                            "fact_refs": [fact_id],
                        }
                    )
            risks: list[dict[str, object]] = []
            for skill in missing_required[:2]:
                if not isinstance(skill, str) or not skill.strip():
                    continue
                fact_id = f"candidate:{candidate_id}:missing-required:{_skill_token(skill)}"
                vacancy_fact = f"vacancy:required-skill:{_skill_token(skill)}"
                refs = [ref for ref in (fact_id, vacancy_fact) if ref in fact_ids]
                if refs:
                    risks.append(
                        {
                            "text": f"Missing required skill {skill.strip()} relative to the vacancy.",
                            "fact_refs": refs,
                        }
                    )
            score_fact = f"candidate:{candidate_id}:match-score"
            if not strengths and score_fact in fact_ids:
                strengths.append(
                    {
                        "text": "System match score is available for relative comparison.",
                        "fact_refs": [score_fact],
                    }
                )
            if not risks and score_fact in fact_ids:
                risks.append(
                    {
                        "text": "Evidence coverage remains limited to supplied match facts.",
                        "fact_refs": [score_fact],
                    }
                )
            assessments.append(
                {
                    "candidate_id": candidate_id,
                    "strengths": strengths[:4],
                    "risks": risks[:4],
                }
            )

        first = ordered_ids[0]
        second = ordered_ids[1]
        first_score_fact = f"candidate:{first}:match-score"
        second_score_fact = f"candidate:{second}:match-score"
        key_refs = [ref for ref in (first_score_fact, second_score_fact) if ref in fact_ids]
        if not key_refs:
            raise MockAiCandidateCompareProviderError("Missing match-score facts for comparison")

        scores: list[tuple[str, int]] = []
        for item in candidates:
            assert isinstance(item, dict)
            candidate_id = str(item["candidate_id"])
            match = item["match"]
            assert isinstance(match, dict)
            score = match.get("score")
            if not isinstance(score, int):
                raise MockAiCandidateCompareProviderError("match.score must be an integer")
            scores.append((candidate_id, score))
        scores.sort(key=lambda pair: (-pair[1], pair[0]))
        leader_id, leader_score = scores[0]
        runner_id, runner_score = scores[1]
        clear_lead = leader_score >= runner_score + 10
        score_refs = [
            ref
            for ref in (
                f"candidate:{leader_id}:match-score",
                f"candidate:{runner_id}:match-score",
            )
            if ref in fact_ids
        ]

        payload: dict[str, object] = {
            "summary": (
                "Candidates differ primarily on system-computed required-skill coverage "
                "and match scores supplied in INPUT."
            ),
            "candidate_assessments": assessments,
            "key_differences": [
                {
                    "text": (
                        "System match scores differ between the leading and trailing candidates."
                    ),
                    "fact_refs": score_refs,
                }
            ],
            "interview_focus_questions": [
                {
                    "question": (
                        "Can you describe a recent project that demonstrates your strongest "
                        "required skill from this vacancy?"
                    ),
                    "candidate_ids": [leader_id],
                    "fact_refs": [f"candidate:{leader_id}:match-score"],
                }
            ],
            "recommended_candidate_id": leader_id,
            "hiring_recommendation": {
                "why_leads": [
                    {
                        "text": (
                            "Stronger required-skill evidence in the supplied match facts"
                            if clear_lead
                            else "Narrow lead on required-skill evidence in the supplied facts"
                        ),
                        "fact_refs": score_refs,
                    }
                ],
                "main_risk": {
                    "text": "Evidence depth beyond employer-safe summaries remains limited.",
                    "fact_refs": key_refs[:2],
                },
                "interview_focus": [
                    {
                        "text": "Validate ownership of strongest required skills",
                        "fact_refs": [f"candidate:{leader_id}:match-score"],
                    },
                    {
                        "text": "Probe recent production delivery decisions",
                        "fact_refs": score_refs,
                    },
                ],
                "alternative_outcome": {
                    "text": (
                        "If interview evidence favors the trailing candidate on ownership, "
                        "that candidate becomes the stronger choice."
                    ),
                    "fact_refs": score_refs,
                },
            },
            "confidence": "medium" if clear_lead else "low",
            "uncertainties": [
                {
                    "text": "Evidence depth beyond employer-safe summaries remains limited.",
                    "fact_refs": key_refs[:2],
                }
            ],
        }
        return AiCandidateCompareLlmPayload.model_validate(payload).model_dump_json()


def _skill_token(name: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in name.strip())
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-") or "skill"
