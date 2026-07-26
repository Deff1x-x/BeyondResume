"""AI Candidate Compare service: deterministic context, LLM call, grounding validation."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Sequence
from dataclasses import dataclass
from hashlib import sha256
import json
import logging
import re
from threading import Lock
from time import monotonic
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.integrations.ai_candidate_compare import (
    generation_mode_for_provider,
    get_ai_candidate_compare_provider,
)
from app.models.employer_candidate_shortlist import EmployerCandidateShortlist
from app.models.vacancy import Vacancy
from app.prompts.ai_candidate_compare import PROMPT_VERSION, SCHEMA_VERSION, SYSTEM_RULES
from app.schemas.ai_candidate_compare import (
    AiCandidateCompareLlmPayload,
    AiCandidateCompareResponse,
    CandidateAssessment,
    GroundedInsight,
    GroundedQuestion,
)
from app.schemas.employer import MatchDetailsEvidenceResponse, MatchDetailsResponse
from app.services.candidate_applications import has_active_application
from app.services.employer import get_vacancy, list_vacancy_requirements
from app.services.employer_candidate_eligibility import (
    EmployerCandidateUnavailableError,
    require_employer_eligible_candidate,
)
from app.services.match_details import (
    MatchDetailsCandidateNotFoundError,
    build_match_details,
)

logger = logging.getLogger(__name__)


class AiCandidateCompareUnavailableError(Exception):
    pass


class AiCandidateCompareCandidateNotFoundError(Exception):
    pass


class AiCandidateCompareVacancyNotFoundError(Exception):
    pass


SERVICE_VERSION = "ai-candidate-compare-service-v1"
CACHE_TTL_SECONDS = 300
CACHE_LIMIT = 128
MAX_DESCRIPTION_CHARS = 2000
MAX_PASSPORT_SKILLS = 8
MAX_EVIDENCE_ITEMS = 5
EVIDENCE_FACT_HASH_PREFIX_LENGTH = 16
CANDIDATE_LABELS = ("Candidate A", "Candidate B", "Candidate C", "Candidate D")

_PROTECTED_PHRASES: tuple[str, ...] = (
    "how old are you",
    "what is your age",
    "your age",
    "date of birth",
    "year you were born",
    "marital status",
    "are you married",
    "do you have children",
    "do you have kids",
    "planning a family",
    "family planning",
    "are you pregnant",
    "pregnancy",
    "maternity leave plans",
    "health condition",
    "medical diagnosis",
    "disability status",
    "your religion",
    "religious beliefs",
    "political views",
    "political affiliation",
    "your race",
    "racial background",
    "ethnic background",
    "ethnicity",
    "your nationality",
    "what gender",
    "your gender",
    "sexual orientation",
    "are you gay",
    "are you lesbian",
)


@dataclass(frozen=True, slots=True)
class AiCandidateCompareContext:
    vacancy_id: UUID
    candidate_ids: tuple[UUID, ...]
    payload: dict[str, object]
    fact_ids: frozenset[str]
    generation_mode: str

    def as_prompt_payload(self) -> dict[str, object]:
        return self.payload


class _Cache:
    def __init__(self) -> None:
        self.items: OrderedDict[str, tuple[float, AiCandidateCompareResponse]] = OrderedDict()
        self.lock = Lock()

    def get(self, key: str) -> AiCandidateCompareResponse | None:
        with self.lock:
            entry = self.items.get(key)
            if entry is None:
                return None
            created_at, value = entry
            if monotonic() - created_at > CACHE_TTL_SECONDS:
                self.items.pop(key, None)
                return None
            self.items.move_to_end(key)
            return value

    def put(self, key: str, value: AiCandidateCompareResponse) -> None:
        with self.lock:
            self.items[key] = (monotonic(), value)
            self.items.move_to_end(key)
            while len(self.items) > CACHE_LIMIT:
                self.items.popitem(last=False)

    def clear(self) -> None:
        with self.lock:
            self.items.clear()


_cache = _Cache()


def clear_ai_candidate_compare_cache() -> None:
    _cache.clear()


def build_ai_candidate_compare_context(
    session: Session,
    *,
    employer_id: UUID,
    vacancy_id: UUID,
    candidate_ids: Sequence[UUID],
) -> AiCandidateCompareContext:
    """Authorize, validate eligibility/shortlist, and build allow-listed facts."""
    vacancy = get_vacancy(session, employer_id, vacancy_id)
    if vacancy is None:
        raise AiCandidateCompareVacancyNotFoundError

    unique_ids = list(dict.fromkeys(candidate_ids))
    if len(unique_ids) != len(candidate_ids):
        # Duplicates should already be rejected by the request schema.
        raise AiCandidateCompareUnavailableError("Duplicate candidate ids")
    if len(unique_ids) < 2 or len(unique_ids) > 4:
        raise AiCandidateCompareUnavailableError("Invalid candidate count")

    ordered_ids = tuple(sorted(unique_ids, key=lambda value: str(value)))
    for candidate_id in ordered_ids:
        try:
            require_employer_eligible_candidate(session, candidate_id)
        except EmployerCandidateUnavailableError as error:
            raise AiCandidateCompareCandidateNotFoundError from error
        if not _is_shortlisted(session, vacancy=vacancy, candidate_id=candidate_id):
            raise AiCandidateCompareCandidateNotFoundError
        if not has_active_application(
            session, vacancy_id=vacancy.id, candidate_id=candidate_id
        ):
            raise AiCandidateCompareCandidateNotFoundError

    requirement_rows = list_vacancy_requirements(session, vacancy_id)
    required_skills = [
        skill.canonical_name
        for requirement, skill in requirement_rows
        if requirement.requirement_type == "required"
    ]
    preferred_skills = [
        skill.canonical_name
        for requirement, skill in requirement_rows
        if requirement.requirement_type == "preferred"
    ]

    facts: dict[str, dict[str, object]] = {}
    vacancy_description = _bounded_text(vacancy.description, MAX_DESCRIPTION_CHARS)
    for skill in required_skills:
        fact_id = f"vacancy:required-skill:{_skill_token(skill)}"
        facts[fact_id] = {"type": "vacancy_required_skill", "skill": skill}
    for skill in preferred_skills:
        fact_id = f"vacancy:preferred-skill:{_skill_token(skill)}"
        facts[fact_id] = {"type": "vacancy_preferred_skill", "skill": skill}

    candidates_payload: list[dict[str, object]] = []
    for index, candidate_id in enumerate(ordered_ids):
        try:
            details = build_match_details(
                session, vacancy_id=vacancy_id, candidate_id=candidate_id
            )
        except MatchDetailsCandidateNotFoundError as error:
            raise AiCandidateCompareCandidateNotFoundError from error
        candidate_payload, candidate_facts = _candidate_payload(
            candidate_id=candidate_id,
            label=CANDIDATE_LABELS[index],
            details=details,
        )
        facts.update(candidate_facts)
        candidates_payload.append(candidate_payload)

    payload: dict[str, object] = {
        "context_version": "ai-candidate-compare-context-v1",
        "vacancy": {
            "id": str(vacancy_id),
            "title": vacancy.title,
            "description": vacancy_description,
            "required_skills": required_skills,
            "preferred_skills": preferred_skills,
        },
        "candidates": candidates_payload,
        "facts": facts,
    }
    return AiCandidateCompareContext(
        vacancy_id=vacancy_id,
        candidate_ids=ordered_ids,
        payload=payload,
        fact_ids=frozenset(facts),
        generation_mode=generation_mode_for_provider(),
    )


def get_ai_candidate_compare(
    context: AiCandidateCompareContext,
) -> AiCandidateCompareResponse:
    """Call the configured provider and return a fully validated response."""
    key = _cache_key(context)
    cached = _cache.get(key)
    if cached is not None:
        return cached

    try:
        provider = get_ai_candidate_compare_provider()
    except Exception as error:
        _log_failure(error, "before_provider_request")
        raise AiCandidateCompareUnavailableError from error
    try:
        content = provider.generate(build_ai_candidate_compare_prompt(context))
    except Exception as error:
        _log_failure(error, "during_provider_request")
        raise AiCandidateCompareUnavailableError from error
    try:
        payload = _parse_json_object(content)
    except Exception as error:
        _log_failure(error, "during_json_parsing")
        raise AiCandidateCompareUnavailableError from error
    if isinstance(payload, dict):
        # generation_mode / vacancy metadata must never be trusted from the model.
        payload.pop("generation_mode", None)
        payload.pop("vacancy_id", None)
        payload.pop("candidate_ids", None)
    try:
        llm_result = AiCandidateCompareLlmPayload.model_validate(payload)
    except Exception as error:
        _log_failure(error, "during_dto_validation")
        raise AiCandidateCompareUnavailableError from error
    try:
        _validate_semantics(llm_result, context)
    except Exception as error:
        _log_failure(error, "during_semantic_validation")
        raise AiCandidateCompareUnavailableError from error

    result = AiCandidateCompareResponse(
        vacancy_id=context.vacancy_id,
        candidate_ids=list(context.candidate_ids),
        generation_mode=context.generation_mode,  # type: ignore[arg-type]
        summary=llm_result.summary,
        candidate_assessments=_ordered_assessments(
            llm_result.candidate_assessments, context.candidate_ids
        ),
        key_differences=llm_result.key_differences,
        interview_focus_questions=llm_result.interview_focus_questions,
        recommended_candidate_id=llm_result.recommended_candidate_id,
        recommendation_rationale=llm_result.recommendation_rationale,
        confidence=llm_result.confidence,
        uncertainties=llm_result.uncertainties,
    )
    _cache.put(key, result)
    return result


def build_ai_candidate_compare_prompt(context: AiCandidateCompareContext) -> str:
    return (
        f"{SYSTEM_RULES}\nINPUT:\n"
        f"{json.dumps(context.as_prompt_payload(), ensure_ascii=False, sort_keys=True)}"
    )


def _candidate_payload(
    *,
    candidate_id: UUID,
    label: str,
    details: MatchDetailsResponse,
) -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    facts: dict[str, dict[str, object]] = {}
    score_fact = f"candidate:{candidate_id}:match-score"
    facts[score_fact] = {"type": "match_score", "score": details.match.score}

    required_matched = list(details.match.required.matched)
    required_missing = list(details.match.required.missing)
    preferred_matched = list(details.match.preferred.matched)
    preferred_missing = list(details.match.preferred.missing)

    for skill in required_matched:
        fact_id = f"candidate:{candidate_id}:matched-required:{_skill_token(skill)}"
        facts[fact_id] = {"type": "matched_required", "skill": skill}
    for skill in required_missing:
        fact_id = f"candidate:{candidate_id}:missing-required:{_skill_token(skill)}"
        facts[fact_id] = {"type": "missing_required", "skill": skill}
    for skill in preferred_matched:
        fact_id = f"candidate:{candidate_id}:matched-preferred:{_skill_token(skill)}"
        facts[fact_id] = {"type": "matched_preferred", "skill": skill}
    for skill in preferred_missing:
        fact_id = f"candidate:{candidate_id}:missing-preferred:{_skill_token(skill)}"
        facts[fact_id] = {"type": "missing_preferred", "skill": skill}

    passport_skills: list[dict[str, object]] = []
    for passport_skill in details.passport.skills[:MAX_PASSPORT_SKILLS]:
        fact_id = f"candidate:{candidate_id}:skill:{_skill_token(passport_skill.name)}"
        facts[fact_id] = {
            "type": "passport_skill",
            "skill": passport_skill.name,
            "evidence_confidence": passport_skill.evidence_confidence,
            "evidence_count": passport_skill.evidence_count,
            "source_types": list(passport_skill.source_types),
        }
        passport_skills.append(
            {
                "name": passport_skill.name,
                "evidence_confidence": passport_skill.evidence_confidence,
                "evidence_count": passport_skill.evidence_count,
                "source_types": list(passport_skill.source_types),
                "fact_id": fact_id,
            }
        )

    evidence_items: list[dict[str, object]] = []
    for evidence in details.evidence[:MAX_EVIDENCE_ITEMS]:
        fact_id = _evidence_fact_id(candidate_id=candidate_id, evidence=evidence)
        # Identical allow-listed evidence content shares one opaque fact_id.
        facts[fact_id] = {
            "type": "evidence_summary",
            "source_type": evidence.source_type,
            "title": evidence.title,
            "verification_status": evidence.verification_status,
            "ownership_status": evidence.ownership_status,
            "skills": list(evidence.skills),
        }
        evidence_items.append(
            {
                "source_type": evidence.source_type,
                "title": evidence.title,
                "verification_status": evidence.verification_status,
                "ownership_status": evidence.ownership_status,
                "skills": list(evidence.skills),
                "fact_id": fact_id,
            }
        )

    payload: dict[str, object] = {
        "candidate_id": str(candidate_id),
        "candidate_label": label,
        "match": {
            "score": details.match.score,
            "required_matched": required_matched,
            "required_missing": required_missing,
            "preferred_matched": preferred_matched,
            "preferred_missing": preferred_missing,
            "score_fact_id": score_fact,
        },
        "passport_summary": {
            "top_skills": list(details.passport.top_skills)[:MAX_PASSPORT_SKILLS],
            "skills": passport_skills,
        },
        "evidence_summaries": evidence_items,
    }
    return payload, facts


def _is_shortlisted(session: Session, *, vacancy: Vacancy, candidate_id: UUID) -> bool:
    entry = session.execute(
        select(EmployerCandidateShortlist.id).where(
            EmployerCandidateShortlist.employer_id == vacancy.employer_id,
            EmployerCandidateShortlist.vacancy_id == vacancy.id,
            EmployerCandidateShortlist.candidate_id == candidate_id,
        )
    ).scalar_one_or_none()
    return entry is not None


def _validate_semantics(
    result: AiCandidateCompareLlmPayload, context: AiCandidateCompareContext
) -> None:
    expected = set(context.candidate_ids)
    assessments = result.candidate_assessments
    assessed_ids = [item.candidate_id for item in assessments]
    if len(assessed_ids) != len(set(assessed_ids)):
        raise AiCandidateCompareUnavailableError("Duplicate candidate assessments")
    if set(assessed_ids) != expected:
        raise AiCandidateCompareUnavailableError("Candidate assessments do not match request")
    if len(assessments) != len(expected):
        raise AiCandidateCompareUnavailableError("Missing candidate assessment")

    if result.recommended_candidate_id is not None:
        if result.recommended_candidate_id not in expected:
            raise AiCandidateCompareUnavailableError("Recommended candidate is not in request")
        if result.recommendation_rationale is None:
            raise AiCandidateCompareUnavailableError("Missing recommendation rationale")
    elif result.recommendation_rationale is not None:
        raise AiCandidateCompareUnavailableError("Unexpected recommendation rationale")

    for assessment in assessments:
        for insight in [*assessment.strengths, *assessment.risks]:
            _assert_insight_grounding(
                insight,
                allowed_candidates={assessment.candidate_id},
                fact_ids=context.fact_ids,
            )
            _assert_safe_text(insight.text)

    for insight in [*result.key_differences, *result.uncertainties]:
        _assert_insight_grounding(
            insight,
            allowed_candidates=expected,
            fact_ids=context.fact_ids,
        )
        _assert_safe_text(insight.text)

    if result.recommendation_rationale is not None:
        _assert_insight_grounding(
            result.recommendation_rationale,
            allowed_candidates=expected,
            fact_ids=context.fact_ids,
        )
        _assert_safe_text(result.recommendation_rationale.text)

    _assert_safe_text(result.summary)

    for question in result.interview_focus_questions:
        question_candidates = set(question.candidate_ids)
        if not question_candidates.issubset(expected):
            raise AiCandidateCompareUnavailableError("Question references unknown candidate")
        _assert_question_grounding(
            question,
            allowed_candidates=question_candidates,
            fact_ids=context.fact_ids,
        )
        _assert_safe_text(question.question)


def _assert_insight_grounding(
    insight: GroundedInsight,
    *,
    allowed_candidates: set[UUID],
    fact_ids: frozenset[str],
) -> None:
    if not insight.fact_refs:
        raise AiCandidateCompareUnavailableError("Insight is missing fact_refs")
    for fact_ref in insight.fact_refs:
        if fact_ref not in fact_ids:
            raise AiCandidateCompareUnavailableError("Unknown fact_ref")
        if not _fact_allowed_for_candidates(fact_ref, allowed_candidates):
            raise AiCandidateCompareUnavailableError("Cross-attributed fact_ref")


def _assert_question_grounding(
    question: GroundedQuestion,
    *,
    allowed_candidates: set[UUID],
    fact_ids: frozenset[str],
) -> None:
    if not question.fact_refs:
        raise AiCandidateCompareUnavailableError("Question is missing fact_refs")
    for fact_ref in question.fact_refs:
        if fact_ref not in fact_ids:
            raise AiCandidateCompareUnavailableError("Unknown fact_ref")
        if not _fact_allowed_for_candidates(fact_ref, allowed_candidates):
            raise AiCandidateCompareUnavailableError("Cross-attributed fact_ref")


def _fact_allowed_for_candidates(fact_ref: str, allowed_candidates: set[UUID]) -> bool:
    if fact_ref.startswith("vacancy:"):
        return True
    for candidate_id in allowed_candidates:
        if fact_ref.startswith(f"candidate:{candidate_id}:"):
            return True
    return False


def _assert_safe_text(value: str) -> None:
    normalized = re.sub(r"[^a-z0-9\s]", " ", value.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    for phrase in _PROTECTED_PHRASES:
        if phrase in normalized:
            raise AiCandidateCompareUnavailableError("Protected language detected")


def _ordered_assessments(
    assessments: Sequence[CandidateAssessment], ordered_ids: Sequence[UUID]
) -> list[CandidateAssessment]:
    by_id = {item.candidate_id: item for item in assessments}
    return [by_id[candidate_id] for candidate_id in ordered_ids]


def _cache_key(context: AiCandidateCompareContext) -> str:
    material = {
        "provider": settings.llm_provider,
        "model": settings.llm_model,
        "prompt_version": PROMPT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "service_version": SERVICE_VERSION,
        "generation_mode": context.generation_mode,
        "vacancy_id": str(context.vacancy_id),
        "candidate_ids": [str(item) for item in context.candidate_ids],
        "payload": context.payload,
        "fact_ids": sorted(context.fact_ids),
    }
    return sha256(
        json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _parse_json_object(content: str) -> object:
    normalized = content.strip()
    if normalized.startswith("```"):
        normalized = normalized.split("\n", 1)[1] if "\n" in normalized else ""
        normalized = normalized.rsplit("```", 1)[0].strip()
    return json.loads(normalized)


def _bounded_text(value: str | None, max_length: int) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if stripped == "":
        return None
    if len(stripped) <= max_length:
        return stripped
    return stripped[:max_length].rstrip()


def _normalize_fact_text(value: str | None) -> str:
    if value is None:
        return ""
    return " ".join(value.strip().casefold().split())


def _evidence_fact_id(
    *,
    candidate_id: UUID,
    evidence: MatchDetailsEvidenceResponse,
) -> str:
    """Opaque deterministic evidence fact id; never embeds titles or free text."""
    source_type = _normalize_fact_text(evidence.source_type)
    title = _normalize_fact_text(evidence.title)
    verification_status = _normalize_fact_text(evidence.verification_status)
    ownership_status = _normalize_fact_text(evidence.ownership_status)
    skills = sorted(
        {
            normalized
            for skill in evidence.skills
            if (normalized := _normalize_fact_text(skill))
        }
    )
    material = {
        "candidate_id": str(candidate_id),
        "ownership_status": ownership_status,
        "skills": skills,
        "source_type": source_type,
        "title": title,
        "verification_status": verification_status,
    }
    digest = sha256(
        json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()
    return (
        f"candidate:{candidate_id}:evidence:{digest[:EVIDENCE_FACT_HASH_PREFIX_LENGTH]}"
    )


def _skill_token(name: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in name.strip())
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-") or "skill"


def _log_failure(error: Exception, stage: str) -> None:
    logger.error(
        "AI Candidate Compare generation failed",
        extra={
            "failure_stage": stage,
            "exception_type": type(error).__name__,
            "exception_message": _safe_error_message(error),
            "http_status": getattr(error, "status_code", None),
            "openai_error_code": getattr(error, "code", None),
        },
    )


def _safe_error_message(error: Exception) -> str:
    if error.__class__.__name__ == "ValidationError" and hasattr(error, "errors"):
        return "; ".join(
            f"{'.'.join(map(str, item.get('loc', ())))}: {item.get('type', 'validation_error')}"
            for item in error.errors()[:10]
        )
    if isinstance(error, json.JSONDecodeError):
        return error.msg
    return str(error)[:500]
