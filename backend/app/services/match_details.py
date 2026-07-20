"""Employer match-details aggregation over existing domain services.

Product layer only: composes Matching, Passport, Roadmap, and Profile.
Does not recompute scores or regenerate passport/roadmap rules.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.candidate_profile import CandidateProfile
from app.schemas.employer import (
    MatchDetailsCandidateResponse,
    MatchDetailsEvidenceResponse,
    MatchDetailsMatchResponse,
    MatchDetailsPassportResponse,
    MatchDetailsResponse,
    MatchDetailsRoadmapItemResponse,
    MatchSkillGroupResponse,
)
from app.schemas.skill_passport import SkillPassportResponse
from app.services.employer import list_vacancy_requirements
from app.services.matching import MatchRequirement, match_passport_to_requirements
from app.services.roadmap import build_roadmap_from_match
from app.services.skill_passport import build_passport

TOP_SKILLS_LIMIT = 6


class MatchDetailsCandidateNotFoundError(Exception):
    """Raised when the candidate profile does not exist."""


def build_match_details(
    session: Session, *, vacancy_id: UUID, candidate_id: UUID
) -> MatchDetailsResponse:
    """Aggregate explainable match context for one candidate against one vacancy."""
    candidate = session.execute(
        select(CandidateProfile).where(CandidateProfile.id == candidate_id)
    ).scalar_one_or_none()
    if candidate is None:
        raise MatchDetailsCandidateNotFoundError

    passport = build_passport(session, candidate_id)
    requirements = [
        MatchRequirement(
            skill_id=skill.id,
            skill_name=skill.canonical_name,
            requirement_type=requirement.requirement_type,
        )
        for requirement, skill in list_vacancy_requirements(session, vacancy_id)
    ]
    match = match_passport_to_requirements(passport, requirements)
    roadmap = build_roadmap_from_match(
        required_missing=match.required.missing,
        preferred_missing=match.preferred.missing,
    )

    name = candidate.display_name.strip() if candidate.display_name else "Unnamed candidate"
    headline = candidate.target_role.strip() if candidate.target_role else None

    return MatchDetailsResponse(
        candidate=MatchDetailsCandidateResponse(
            id=candidate.id,
            name=name,
            headline=headline,
            avatar=None,
        ),
        match=MatchDetailsMatchResponse(
            score=match.score,
            required=MatchSkillGroupResponse(
                matched=list(match.required.matched),
                missing=list(match.required.missing),
            ),
            preferred=MatchSkillGroupResponse(
                matched=list(match.preferred.matched),
                missing=list(match.preferred.missing),
            ),
        ),
        passport=MatchDetailsPassportResponse(
            top_skills=[skill.name for skill in passport.skills[:TOP_SKILLS_LIMIT]]
        ),
        evidence=_evidence_from_passport(passport),
        roadmap=[
            MatchDetailsRoadmapItemResponse(
                id=item.id,
                title=item.title,
                reason=item.reason,
                priority=item.priority,
                missing_skills=list(item.missing_skills),
                related_skills=list(item.related_skills),
            )
            for item in roadmap.items
        ],
    )


def _evidence_from_passport(
    passport: SkillPassportResponse,
) -> list[MatchDetailsEvidenceResponse]:
    """Invert passport skill→evidence nesting into evidence→skills for the UI."""
    by_id: dict[UUID, MatchDetailsEvidenceResponse] = {}
    skill_names_by_evidence: dict[UUID, list[str]] = {}

    for skill in passport.skills:
        for evidence in skill.evidence:
            if evidence.id not in by_id:
                by_id[evidence.id] = MatchDetailsEvidenceResponse(
                    source_type=evidence.source_type,
                    title=evidence.title,
                    skills=[],
                )
                skill_names_by_evidence[evidence.id] = []
            names = skill_names_by_evidence[evidence.id]
            if skill.name not in names:
                names.append(skill.name)

    items = [
        MatchDetailsEvidenceResponse(
            source_type=item.source_type,
            title=item.title,
            skills=sorted(skill_names_by_evidence[evidence_id], key=str.lower),
        )
        for evidence_id, item in by_id.items()
    ]
    items.sort(key=lambda entry: ((entry.title or "").lower(), entry.source_type))
    return items
