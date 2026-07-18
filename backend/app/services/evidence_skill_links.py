from dataclasses import dataclass
from decimal import Decimal
import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evidence_skill_link import EvidenceSkillLink
from app.models.evidence_unit import EvidenceUnit
from app.models.skill import Skill


class EvidenceSkillLinkCandidateMismatchError(Exception):
    """Raised when link candidate_id differs from its EvidenceUnit candidate_id."""


class InvalidExtractionMethodError(ValueError):
    """Raised when an extraction method is not permitted."""


class InvalidExtractionVersionError(ValueError):
    """Raised when an extraction version is empty or invalid."""


class InvalidExtractionConfidenceError(ValueError):
    """Raised when extraction confidence is outside the allowed range."""


class InvalidExtractionContextError(ValueError):
    """Raised when extraction context is not a JSON object."""


@dataclass(frozen=True, slots=True)
class EvidenceSkillLinkPersistenceResult:
    link: EvidenceSkillLink
    created: bool
    changed: bool


_EXTRACTION_METHODS = frozenset({"deterministic", "ai", "manual"})


def persist_evidence_skill_link(
    session: Session,
    *,
    candidate_id: UUID,
    evidence_unit: EvidenceUnit,
    skill: Skill,
    extraction_method: str,
    extraction_version: str,
    extraction_confidence: Decimal,
    context: dict[str, object],
) -> EvidenceSkillLinkPersistenceResult:
    if candidate_id != evidence_unit.candidate_id:
        raise EvidenceSkillLinkCandidateMismatchError
    _validate_extraction_method(extraction_method)
    version = _validate_extraction_version(extraction_version)
    confidence = _validate_extraction_confidence(extraction_method, extraction_confidence)
    context_copy = _validate_and_copy_context(context)
    link = session.execute(
        select(EvidenceSkillLink).where(
            EvidenceSkillLink.evidence_unit_id == evidence_unit.id,
            EvidenceSkillLink.skill_id == skill.id,
            EvidenceSkillLink.extraction_method == extraction_method,
            EvidenceSkillLink.extraction_version == version,
        )
    ).scalar_one_or_none()
    if link is None:
        link = EvidenceSkillLink(
            candidate_id=candidate_id,
            evidence_unit_id=evidence_unit.id,
            skill_id=skill.id,
            extraction_method=extraction_method,
            extraction_version=version,
            extraction_confidence=confidence,
            context=context_copy,
        )
        session.add(link)
        session.flush()
        return EvidenceSkillLinkPersistenceResult(link=link, created=True, changed=True)
    if link.extraction_confidence == confidence and link.context == context_copy:
        return EvidenceSkillLinkPersistenceResult(link=link, created=False, changed=False)
    link.extraction_confidence = confidence
    link.context = context_copy
    session.flush()
    return EvidenceSkillLinkPersistenceResult(link=link, created=False, changed=True)


def _validate_extraction_method(extraction_method: str) -> None:
    if extraction_method not in _EXTRACTION_METHODS:
        raise InvalidExtractionMethodError


def _validate_extraction_version(extraction_version: str) -> str:
    if not isinstance(extraction_version, str):
        raise InvalidExtractionVersionError
    version = extraction_version.strip()
    if not version:
        raise InvalidExtractionVersionError
    return version


def _validate_extraction_confidence(
    extraction_method: str, extraction_confidence: Decimal
) -> Decimal:
    if not isinstance(extraction_confidence, Decimal) or not (
        Decimal("0.00") <= extraction_confidence <= Decimal("1.00")
    ):
        raise InvalidExtractionConfidenceError
    if extraction_method in {"deterministic", "manual"} and extraction_confidence != Decimal(
        "1.00"
    ):
        raise InvalidExtractionConfidenceError
    return extraction_confidence


def _validate_and_copy_context(context: dict[str, object]) -> dict[str, object]:
    if not isinstance(context, dict):
        raise InvalidExtractionContextError
    try:
        copied_context = json.loads(json.dumps(context, ensure_ascii=False, allow_nan=False))
    except (TypeError, ValueError) as error:
        raise InvalidExtractionContextError from error
    if not isinstance(copied_context, dict):
        raise InvalidExtractionContextError
    return copied_context
