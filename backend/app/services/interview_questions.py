"""AI Interview Questions service: context, cache, generation, and safety."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from hashlib import sha256
import json
import logging
from threading import Lock
from time import monotonic
from uuid import UUID

from typing import Sequence, TypedDict

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.integrations.interview_questions import get_interview_questions_provider
from app.prompts.interview_questions import PROMPT_VERSION, SCHEMA_VERSION, SYSTEM_RULES
from app.schemas.employer import MatchDetailsResponse, MatchedSkillDetailsResponse
from app.schemas.interview_questions import InterviewQuestionsResponse
from app.services.employer import get_vacancy, list_vacancy_requirements
from app.services.skill_passport import build_passport

logger = logging.getLogger(__name__)

SERVICE_VERSION = "interview-questions-service-v1"
CACHE_TTL_SECONDS = 300
CACHE_LIMIT = 128
_MAX_EVIDENCE_TITLE_LENGTH = 200
_MAX_VACANCY_DESCRIPTION_LENGTH = 2000


class _PassportSkillRow(TypedDict):
    name: str
    confidence: int
    evidence_count: int
    source_types: list[str]


class InterviewQuestionsUnavailableError(Exception):
    """Interview questions could not be generated safely."""


@dataclass(frozen=True, slots=True)
class InterviewQuestionsContext:
    vacancy_id: str
    candidate_id: str
    facts: dict[str, object]
    gaps: dict[str, object]

    def as_payload(self) -> dict[str, object]:
        return {
            "FACTS": self.facts,
            "GAPS": self.gaps,
        }

    def cache_fingerprint(self) -> dict[str, object]:
        return {
            "vacancy_id": self.vacancy_id,
            "candidate_id": self.candidate_id,
            "facts": self.facts,
            "gaps": self.gaps,
        }


class _Cache:
    def __init__(self) -> None:
        self.items: OrderedDict[str, tuple[float, InterviewQuestionsResponse]] = OrderedDict()
        self.lock = Lock()

    def get(self, key: str) -> InterviewQuestionsResponse | None:
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

    def put(self, key: str, value: InterviewQuestionsResponse) -> None:
        with self.lock:
            self.items[key] = (monotonic(), value)
            self.items.move_to_end(key)
            while len(self.items) > CACHE_LIMIT:
                self.items.popitem(last=False)

    def clear(self) -> None:
        with self.lock:
            self.items.clear()


_cache = _Cache()

# Phrase markers only — avoid single ambiguous tokens like "race" or "family".
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


def build_interview_questions_context(
    session: Session,
    *,
    employer_id: UUID,
    vacancy_id: UUID,
    candidate_id: UUID,
    details: MatchDetailsResponse,
) -> InterviewQuestionsContext:
    """Assemble allow-listed FACTS/GAPS from deterministic match data only."""
    vacancy = get_vacancy(session, employer_id, vacancy_id)
    if vacancy is None:
        raise InterviewQuestionsUnavailableError("Vacancy not found")

    requirement_rows = list_vacancy_requirements(session, vacancy_id)
    required_skills = sorted(
        (
            skill.canonical_name
            for requirement, skill in requirement_rows
            if requirement.requirement_type == "required"
        ),
        key=str.casefold,
    )
    preferred_skills = sorted(
        (
            skill.canonical_name
            for requirement, skill in requirement_rows
            if requirement.requirement_type == "preferred"
        ),
        key=str.casefold,
    )

    passport = build_passport(session, candidate_id)
    passport_skills: list[_PassportSkillRow] = sorted(
        (
            {
                "name": skill.name,
                "confidence": round(skill.evidence_confidence * 100),
                "evidence_count": skill.evidence_count,
                "source_types": sorted({item.source_type for item in skill.evidence}),
            }
            for skill in passport.skills
        ),
        key=lambda item: (-item["confidence"], item["name"].casefold()),
    )

    matched_required = _matched_skill_rows(details.match.required.matched_details)
    matched_preferred = _matched_skill_rows(details.match.preferred.matched_details)
    if not matched_required:
        matched_required = [
            {"name": name, "evidence_title": None, "evidence_basis": None, "confidence": None}
            for name in sorted(details.match.required.matched, key=str.casefold)
        ]
    if not matched_preferred:
        matched_preferred = [
            {"name": name, "evidence_title": None, "evidence_basis": None, "confidence": None}
            for name in sorted(details.match.preferred.matched, key=str.casefold)
        ]

    evidence_summaries = sorted(
        (
            {
                "title": title,
                "source_type": item.source_type,
            }
            for item in details.evidence
            if (title := _bounded_text(item.title, max_length=_MAX_EVIDENCE_TITLE_LENGTH))
            is not None
        ),
        key=lambda item: (
            str(item["source_type"]).casefold(),
            str(item["title"] or "").casefold(),
        ),
    )

    facts: dict[str, object] = {
        "vacancy_title": vacancy.title,
        "vacancy_description": _bounded_text(
            vacancy.description, max_length=_MAX_VACANCY_DESCRIPTION_LENGTH
        ),
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "match_percentage": details.match.score,
        "candidate_headline": details.candidate.headline,
        "matched_required_skills": matched_required,
        "matched_preferred_skills": matched_preferred,
        "passport_skills": passport_skills,
        "evidence_summaries": evidence_summaries,
    }
    gaps: dict[str, object] = {
        "missing_required_skills": sorted(details.match.required.missing, key=str.casefold),
        "missing_preferred_skills": sorted(details.match.preferred.missing, key=str.casefold),
        "low_confidence_required_skills": [
            {
                "name": skill["name"],
                "confidence": skill["confidence"],
            }
            for skill in passport_skills
            if skill["name"] in set(details.match.required.matched) and skill["confidence"] < 50
        ],
    }
    return InterviewQuestionsContext(
        vacancy_id=str(vacancy_id),
        candidate_id=str(candidate_id),
        facts=facts,
        gaps=gaps,
    )


def build_interview_questions_prompt(context: InterviewQuestionsContext) -> str:
    return (
        f"{SYSTEM_RULES}\nINPUT:\n"
        f"{json.dumps(context.as_payload(), ensure_ascii=False, sort_keys=True)}"
    )


def get_interview_questions(
    context: InterviewQuestionsContext,
    *,
    refresh: bool = False,
) -> InterviewQuestionsResponse:
    key = _cache_key(context)
    if not refresh:
        cached = _cache.get(key)
        if cached is not None:
            return cached

    try:
        provider = get_interview_questions_provider()
    except Exception as error:
        _log_failure(error, "before_provider_request")
        raise InterviewQuestionsUnavailableError from error
    try:
        content = provider.generate(build_interview_questions_prompt(context))
    except Exception as error:
        _log_failure(error, "during_provider_request")
        raise InterviewQuestionsUnavailableError from error
    try:
        result = parse_interview_questions_response(content)
    except InterviewQuestionsUnavailableError:
        raise
    except Exception as error:
        _log_failure(error, "during_response_validation")
        raise InterviewQuestionsUnavailableError from error

    _cache.put(key, result)
    return result


def parse_interview_questions_response(content: str) -> InterviewQuestionsResponse:
    try:
        payload = _parse_json_object(content)
    except Exception as error:
        raise InterviewQuestionsUnavailableError("Provider response was not valid JSON") from error
    try:
        result = InterviewQuestionsResponse.model_validate(payload)
    except ValidationError as error:
        raise InterviewQuestionsUnavailableError(
            "Provider response did not match the interview questions schema"
        ) from error
    _assert_safe_questions(result)
    return result


def _assert_safe_questions(response: InterviewQuestionsResponse) -> None:
    for item in response.questions:
        normalized = _normalize_for_safety(item.question)
        for phrase in _PROTECTED_PHRASES:
            if phrase in normalized:
                raise InterviewQuestionsUnavailableError("Provider response failed safety checks")


def _normalize_for_safety(value: str) -> str:
    lowered = value.casefold()
    cleaned: list[str] = []
    for char in lowered:
        if char.isalnum() or char.isspace():
            cleaned.append(char)
        else:
            cleaned.append(" ")
    return " ".join("".join(cleaned).split())


def _matched_skill_rows(
    details: Sequence[MatchedSkillDetailsResponse],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for detail in details:
        skill_name = detail.skill_name
        if not skill_name.strip():
            continue
        evidence_list = detail.evidence or []
        evidence_title: str | None = None
        source_types: list[str] = []
        confidence: float | None = None
        for evidence in evidence_list:
            if evidence_title is None:
                evidence_title = _bounded_text(
                    evidence.title, max_length=_MAX_EVIDENCE_TITLE_LENGTH
                )
            source_type = evidence.source_type
            if isinstance(source_type, str) and source_type.strip():
                source_types.append(source_type.strip())
            evidence_confidence = evidence.evidence_confidence
            if confidence is None:
                confidence = round(float(evidence_confidence) * 100)
        evidence_basis = None
        if source_types:
            unique_sources = sorted(set(source_types), key=str.casefold)
            evidence_basis = _bounded_text(
                f"Sources: {', '.join(unique_sources)}",
                max_length=_MAX_EVIDENCE_TITLE_LENGTH,
            )
        rows.append(
            {
                "name": skill_name.strip(),
                "evidence_title": evidence_title,
                "evidence_basis": evidence_basis,
                "confidence": confidence,
            }
        )
    return sorted(rows, key=lambda item: str(item["name"]).casefold())


def _bounded_text(value: str | None, *, max_length: int) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    stripped = " ".join(value.split()).strip()
    if stripped == "":
        return None
    if len(stripped) <= max_length:
        return stripped
    return stripped[:max_length].rstrip()


def _cache_key(context: InterviewQuestionsContext) -> str:
    material = {
        "provider": settings.llm_provider,
        "model": settings.llm_model,
        "prompt_version": PROMPT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "service_version": SERVICE_VERSION,
        "fingerprint": context.cache_fingerprint(),
    }
    return sha256(
        json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _parse_json_object(content: str) -> object:
    normalized = content.strip()
    if not normalized:
        raise InterviewQuestionsUnavailableError("Provider response was empty")
    if normalized.startswith("```"):
        normalized = normalized.split("\n", 1)[1] if "\n" in normalized else ""
        normalized = normalized.rsplit("```", 1)[0].strip()
    return json.loads(normalized)


def _log_failure(error: Exception, stage: str) -> None:
    logger.error(
        "AI Interview Questions generation failed",
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


def clear_interview_questions_cache() -> None:
    _cache.clear()
