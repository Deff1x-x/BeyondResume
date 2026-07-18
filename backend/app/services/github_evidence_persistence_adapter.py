"""Persistence boundary for deterministic GitHub evidence link values."""

from __future__ import annotations

from collections.abc import Mapping

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evidence_unit import EvidenceUnit
from app.models.skill import Skill
from app.services.evidence_skill_links import (
    EvidenceSkillLinkPersistenceResult,
    InvalidExtractionContextError,
    persist_evidence_skill_link,
)
from app.services.github_evidence_skill_link_builder import GitHubEvidenceSkillLinkValues
from app.services.skill_ontology import SkillNotFoundError


class EvidenceUnitNotFoundError(Exception):
    """Raised when GitHub evidence values reference an unknown EvidenceUnit."""


def persist_github_evidence_skill_link(
    session: Session,
    values: GitHubEvidenceSkillLinkValues,
) -> EvidenceSkillLinkPersistenceResult:
    """Load link entities and delegate persistence of one GitHub evidence command."""
    evidence_unit = session.execute(
        select(EvidenceUnit).where(EvidenceUnit.id == values.evidence_unit_id)
    ).scalar_one_or_none()
    if evidence_unit is None:
        raise EvidenceUnitNotFoundError

    skill = session.execute(select(Skill).where(Skill.id == values.skill_id)).scalar_one_or_none()
    if skill is None:
        raise SkillNotFoundError

    return persist_evidence_skill_link(
        session,
        candidate_id=values.candidate_id,
        evidence_unit=evidence_unit,
        skill=skill,
        extraction_method=values.extraction_method,
        extraction_version=values.extraction_version,
        extraction_confidence=values.extraction_confidence,
        context=_deep_thaw_context(values.context),
    )


def _deep_thaw_context(context: Mapping[str, object]) -> dict[str, object]:
    """Convert the immutable command representation to JSON-compatible mutable containers."""
    thawed = _deep_thaw_value(context)
    if not isinstance(thawed, dict):
        raise InvalidExtractionContextError
    return thawed


def _deep_thaw_value(value: object) -> object:
    if isinstance(value, Mapping):
        thawed_mapping: dict[str, object] = {}
        for key, nested_value in value.items():
            if not isinstance(key, str):
                raise InvalidExtractionContextError
            thawed_mapping[key] = _deep_thaw_value(nested_value)
        return thawed_mapping
    if isinstance(value, tuple):
        return [_deep_thaw_value(item) for item in value]
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise InvalidExtractionContextError
