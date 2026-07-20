"""Skill Passport aggregation over EvidenceSkillLink data."""

from collections.abc import Mapping
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evidence_skill_link import EvidenceSkillLink
from app.models.evidence_unit import EvidenceUnit
from app.models.skill import Skill
from app.schemas.skill_passport import (
    SkillPassportEvidenceResponse,
    SkillPassportResponse,
    SkillPassportSkillResponse,
)
from app.services.skill_confidence import (
    SkillEvidenceObservation,
    calculate_skill_confidence,
)


def empty_passport() -> SkillPassportResponse:
    return SkillPassportResponse(skills=[], total_skills=0, total_evidence=0)


def build_passport(session: Session, candidate_id: UUID) -> SkillPassportResponse:
    rows = session.execute(
        select(Skill, EvidenceUnit, EvidenceSkillLink.context)
        .join(EvidenceSkillLink, EvidenceSkillLink.skill_id == Skill.id)
        .join(EvidenceUnit, EvidenceUnit.id == EvidenceSkillLink.evidence_unit_id)
        .where(
            EvidenceSkillLink.candidate_id == candidate_id,
            Skill.deprecated.is_(False),
        )
    ).all()

    observations_by_skill: dict[UUID, dict[UUID, SkillEvidenceObservation]] = {}
    skills_by_id: dict[UUID, Skill] = {}
    evidence_by_id: dict[UUID, EvidenceUnit] = {}
    for skill, evidence_unit, context in rows:
        if skill.deprecated:
            continue
        skills_by_id[skill.id] = skill
        evidence_by_id[evidence_unit.id] = evidence_unit
        observations_by_evidence = observations_by_skill.setdefault(skill.id, {})
        existing_observation = observations_by_evidence.get(evidence_unit.id)
        observations_by_evidence[evidence_unit.id] = SkillEvidenceObservation(
            source_type=evidence_unit.source_type,
            source_reference=evidence_unit.source_reference,
            quality_flags=evidence_unit.quality_flags,
            context=_merge_context(
                existing_observation.context if existing_observation else None,
                context if isinstance(context, dict) else None,
            ),
        )

    skill_responses: list[SkillPassportSkillResponse] = []
    for skill_id, observations_by_evidence in observations_by_skill.items():
        skill = skills_by_id[skill_id]
        evidence_ids = tuple(observations_by_evidence)
        confidence = calculate_skill_confidence(tuple(observations_by_evidence.values()))
        evidence_responses = sorted(
            (
                SkillPassportEvidenceResponse(
                    id=evidence_id,
                    title=evidence_by_id[evidence_id].title,
                    description=evidence_by_id[evidence_id].description,
                    source_type=evidence_by_id[evidence_id].source_type,
                    source_reference=evidence_by_id[evidence_id].source_reference,
                    evidence_confidence=confidence.evidence_confidences[index],
                )
                for index, evidence_id in enumerate(evidence_ids)
            ),
            key=lambda item: (-item.evidence_confidence, item.title or ""),
        )
        skill_responses.append(
            SkillPassportSkillResponse(
                id=skill.id,
                name=skill.canonical_name,
                category=skill.category,
                evidence_confidence=confidence.confidence,
                evidence_count=len(observations_by_evidence),
                evidence=evidence_responses,
            )
        )

    skill_responses.sort(key=lambda item: (-item.evidence_confidence, item.name.lower()))
    return SkillPassportResponse(
        skills=skill_responses,
        total_skills=len(skill_responses),
        total_evidence=len(evidence_by_id),
    )


def _merge_context(
    existing: Mapping[str, object] | None,
    incoming: Mapping[str, object] | None,
) -> dict[str, object] | None:
    """Merge link signals for one Evidence–Skill pair deterministically."""
    signals: list[object] = []
    for context in (existing, incoming):
        if not context:
            continue
        value = context.get("signals")
        if not isinstance(value, list):
            continue
        for signal in value:
            if signal not in signals:
                signals.append(signal)
    return {"signals": signals} if signals else None
