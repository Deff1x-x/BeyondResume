"""Employer match-details aggregation over existing domain services.

Product layer only: composes Matching, Passport, Roadmap, and Profile.
Does not recompute scores or regenerate passport/roadmap rules.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evidence_skill_link import EvidenceSkillLink
from app.schemas.employer import (
    EvidenceSuggestionResponse,
    MatchDetailsCandidateResponse,
    MatchDetailsEvidenceResponse,
    MatchDetailsMatchResponse,
    MatchDetailsPassportResponse,
    MatchDetailsPassportSkillResponse,
    MatchDetailsResponse,
    MatchDetailsRoadmapItemResponse,
    MatchedSkillDetailsResponse,
    MatchedSkillEvidenceResponse,
    MatchSkillGroupResponse,
    MissingSkillDetailsResponse,
    SignalSummaryResponse,
)
from app.schemas.skill_passport import (
    SkillPassportEvidenceResponse,
    SkillPassportResponse,
    SkillPassportSkillResponse,
)
from app.services.employer import list_vacancy_requirements
from app.services.employer_candidate_eligibility import (
    EmployerCandidateUnavailableError,
    require_employer_eligible_candidate,
    trimmed_candidate_display_name,
)
from app.services.candidate_applications import has_active_application
from app.services.matching import MatchRequirement, match_passport_to_requirements
from app.services.roadmap import build_roadmap_from_match
from app.services.signal_summaries import public_categories_for_evidence
from app.services.skill_gap_suggestions import evidence_suggestion_categories
from app.services.skill_passport import build_passport

TOP_SKILLS_LIMIT = 6

LinkContextIndex = dict[tuple[UUID, UUID], list[Mapping[str, object] | None]]


class MatchDetailsCandidateNotFoundError(Exception):
    """Raised when the candidate is missing or not eligible for employer workflows."""


def build_match_details(
    session: Session, *, vacancy_id: UUID, candidate_id: UUID
) -> MatchDetailsResponse:
    """Aggregate explainable match context for one candidate against one vacancy."""
    try:
        candidate = require_employer_eligible_candidate(session, candidate_id)
    except EmployerCandidateUnavailableError as error:
        raise MatchDetailsCandidateNotFoundError from error

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

    passport_skill_ids = {skill.id for skill in passport.skills}
    matched_skill_ids = {
        requirement.skill_id
        for requirement in requirements
        if requirement.skill_id in passport_skill_ids
    }
    link_contexts = _fetch_evidence_link_contexts(
        session, candidate_id=candidate_id, skill_ids=matched_skill_ids
    )

    name = trimmed_candidate_display_name(candidate)
    if name is None:
        # Defensive: eligibility already requires a non-empty name.
        raise MatchDetailsCandidateNotFoundError
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
                matched_details=_matched_details_for_group(
                    requirements=requirements,
                    requirement_type="required",
                    passport=passport,
                    link_contexts=link_contexts,
                ),
                missing_details=_missing_details_for_group(
                    requirements=requirements,
                    requirement_type="required",
                    passport_skill_ids=passport_skill_ids,
                ),
            ),
            preferred=MatchSkillGroupResponse(
                matched=list(match.preferred.matched),
                missing=list(match.preferred.missing),
                matched_details=_matched_details_for_group(
                    requirements=requirements,
                    requirement_type="preferred",
                    passport=passport,
                    link_contexts=link_contexts,
                ),
                missing_details=_missing_details_for_group(
                    requirements=requirements,
                    requirement_type="preferred",
                    passport_skill_ids=passport_skill_ids,
                ),
            ),
        ),
        passport=MatchDetailsPassportResponse(
            top_skills=[skill.name for skill in passport.skills[:TOP_SKILLS_LIMIT]],
            skills=_employer_safe_passport_skills(passport),
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
        has_applied=has_active_application(
            session, vacancy_id=vacancy_id, candidate_id=candidate_id
        ),
    )


def _fetch_evidence_link_contexts(
    session: Session,
    *,
    candidate_id: UUID,
    skill_ids: set[UUID],
) -> LinkContextIndex:
    """Batch-load link contexts for matched skills of one candidate.

    Selects only skill_id, evidence_unit_id, and context — never raw payloads.
    """
    if not skill_ids:
        return {}
    rows = session.execute(
        select(
            EvidenceSkillLink.skill_id,
            EvidenceSkillLink.evidence_unit_id,
            EvidenceSkillLink.context,
        ).where(
            EvidenceSkillLink.candidate_id == candidate_id,
            EvidenceSkillLink.skill_id.in_(skill_ids),
        )
    ).all()
    contexts_by_pair: LinkContextIndex = defaultdict(list)
    for skill_id, evidence_unit_id, context in rows:
        contexts_by_pair[(skill_id, evidence_unit_id)].append(
            context if isinstance(context, Mapping) else None
        )
    return dict(contexts_by_pair)


def _employer_safe_passport_skills(
    passport: SkillPassportResponse,
) -> list[MatchDetailsPassportSkillResponse]:
    """Project existing passport results without candidate-private evidence details."""
    return [
        MatchDetailsPassportSkillResponse(
            name=skill.name,
            evidence_confidence=skill.evidence_confidence,
            evidence_count=skill.evidence_count,
            source_types=sorted({evidence.source_type for evidence in skill.evidence}),
        )
        for skill in passport.skills
    ]


def _matched_details_for_group(
    *,
    requirements: list[MatchRequirement],
    requirement_type: str,
    passport: SkillPassportResponse,
    link_contexts: LinkContextIndex,
) -> list[MatchedSkillDetailsResponse]:
    """Project matched requirements onto passport evidence by Skill.id.

    Uses the same binary ownership check as matching (``skill_id in passport``)
    without recomputing the score. ``MatchResult.matched`` / ``missing`` remain
    the public name lists.
    """
    passport_by_id: dict[UUID, SkillPassportSkillResponse] = {
        skill.id: skill for skill in passport.skills
    }
    details: list[MatchedSkillDetailsResponse] = []
    for requirement in requirements:
        if requirement.requirement_type != requirement_type:
            continue
        skill = passport_by_id.get(requirement.skill_id)
        if skill is None:
            continue
        details.append(
            MatchedSkillDetailsResponse(
                skill_id=skill.id,
                skill_name=skill.name,
                evidence=[
                    _employer_safe_matched_evidence(
                        skill_id=skill.id,
                        evidence=item,
                        link_contexts=link_contexts,
                    )
                    for item in skill.evidence
                ],
            )
        )
    return details


def _missing_details_for_group(
    *,
    requirements: list[MatchRequirement],
    requirement_type: str,
    passport_skill_ids: set[UUID],
) -> list[MissingSkillDetailsResponse]:
    """Explain which evidence categories could confirm each missing requirement.

    Uses the same owned-skill-id set and the same requirement order as
    ``MatchResult.missing``, so the two lists stay index-for-index aligned.
    Suggestions come from the static rule registries only — no candidate data.
    """
    return [
        MissingSkillDetailsResponse(
            skill_id=requirement.skill_id,
            skill_name=requirement.skill_name,
            evidence_suggestions=[
                EvidenceSuggestionResponse(category=category)
                for category in evidence_suggestion_categories(requirement.skill_name)
            ],
        )
        for requirement in requirements
        if requirement.requirement_type == requirement_type
        and requirement.skill_id not in passport_skill_ids
    ]


def _employer_safe_matched_evidence(
    *,
    skill_id: UUID,
    evidence: SkillPassportEvidenceResponse,
    link_contexts: LinkContextIndex,
) -> MatchedSkillEvidenceResponse:
    contexts: Sequence[Mapping[str, object] | None] = link_contexts.get((skill_id, evidence.id), ())
    categories = public_categories_for_evidence(
        source_type=evidence.source_type,
        contexts=contexts,
    )
    return MatchedSkillEvidenceResponse(
        id=evidence.id,
        source_type=evidence.source_type,
        title=evidence.title,
        verification_status=evidence.verification_status,
        ownership_status=evidence.ownership_status,
        evidence_confidence=evidence.evidence_confidence,
        signal_summaries=[SignalSummaryResponse(category=category) for category in categories],
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
                    verification_status=evidence.verification_status,
                    ownership_status=evidence.ownership_status,
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
            verification_status=item.verification_status,
            ownership_status=item.ownership_status,
            skills=sorted(skill_names_by_evidence[evidence_id], key=str.lower),
        )
        for evidence_id, item in by_id.items()
    ]
    items.sort(key=lambda entry: ((entry.title or "").lower(), entry.source_type))
    return items
