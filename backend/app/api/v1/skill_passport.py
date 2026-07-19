from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import require_candidate
from app.db.session import get_db
from app.models.evidence_skill_link import EvidenceSkillLink
from app.models.evidence_unit import EvidenceUnit
from app.models.skill import Skill
from app.models.user import User
from app.schemas.skill_passport import (
    SkillPassportEvidenceResponse,
    SkillPassportResponse,
    SkillPassportSkillResponse,
)
from app.services.candidate import get_candidate_profile

router = APIRouter(prefix="/candidate/skill-passport", tags=["skill-passport"])


def _empty_passport() -> SkillPassportResponse:
    return SkillPassportResponse(skills=[], total_skills=0, total_evidence=0)


def _build_passport(session: Session, candidate_id: UUID) -> SkillPassportResponse:
    rows = session.execute(
        select(Skill, EvidenceUnit, EvidenceSkillLink.extraction_confidence)
        .join(EvidenceSkillLink, EvidenceSkillLink.skill_id == Skill.id)
        .join(EvidenceUnit, EvidenceUnit.id == EvidenceSkillLink.evidence_unit_id)
        .where(
            EvidenceSkillLink.candidate_id == candidate_id,
            Skill.deprecated.is_(False),
        )
    ).all()

    # Multiple links may connect the same (skill, evidence) pair through
    # different extraction methods or versions; keep the strongest one.
    # evidence_confidence is the strength of the Evidence↔Skill link, not
    # a proficiency / skill-level score.
    link_confidence: dict[UUID, dict[UUID, float]] = {}
    skills_by_id: dict[UUID, Skill] = {}
    evidence_by_id: dict[UUID, EvidenceUnit] = {}
    for skill, evidence_unit, extraction_confidence in rows:
        if skill.deprecated:
            continue
        skills_by_id[skill.id] = skill
        evidence_by_id[evidence_unit.id] = evidence_unit
        per_skill = link_confidence.setdefault(skill.id, {})
        per_skill[evidence_unit.id] = max(
            per_skill.get(evidence_unit.id, 0.0), float(extraction_confidence)
        )

    skill_responses: list[SkillPassportSkillResponse] = []
    for skill_id, per_skill in link_confidence.items():
        skill = skills_by_id[skill_id]
        evidence_responses = sorted(
            (
                SkillPassportEvidenceResponse(
                    id=evidence_id,
                    title=evidence_by_id[evidence_id].title,
                    description=evidence_by_id[evidence_id].description,
                    source_type=evidence_by_id[evidence_id].source_type,
                    source_reference=evidence_by_id[evidence_id].source_reference,
                    evidence_confidence=link_score,
                )
                for evidence_id, link_score in per_skill.items()
            ),
            key=lambda item: (-item.evidence_confidence, item.title or ""),
        )
        skill_responses.append(
            SkillPassportSkillResponse(
                id=skill.id,
                name=skill.canonical_name,
                category=skill.category,
                evidence_confidence=max(per_skill.values()),
                evidence_count=len(per_skill),
                evidence=evidence_responses,
            )
        )

    skill_responses.sort(key=lambda item: (-item.evidence_confidence, item.name.lower()))
    return SkillPassportResponse(
        skills=skill_responses,
        total_skills=len(skill_responses),
        total_evidence=len(evidence_by_id),
    )


@router.get("", response_model=SkillPassportResponse)
def get_skill_passport(
    current_user: Annotated[User, Depends(require_candidate)],
    session: Annotated[Session, Depends(get_db)],
) -> SkillPassportResponse:
    profile = get_candidate_profile(session, current_user.id)
    if profile is None:
        return _empty_passport()
    return _build_passport(session, profile.id)
