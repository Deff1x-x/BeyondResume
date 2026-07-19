"""Deterministic vacancy↔candidate matching over Skill Passport and requirements.

No AI, no text analysis, no Session/API dependencies. Matching is based only on
Skill IDs present in the passport versus VacancySkillRequirement rows.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.schemas.skill_passport import SkillPassportResponse

# Required skills dominate the score; preferred fill the remainder.
REQUIRED_WEIGHT = 70
PREFERRED_WEIGHT = 30


@dataclass(frozen=True, slots=True)
class MatchRequirement:
    skill_id: UUID
    skill_name: str
    requirement_type: str  # "required" | "preferred"


@dataclass(frozen=True, slots=True)
class SkillGroupBreakdown:
    matched: tuple[str, ...]
    missing: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MatchResult:
    score: int
    required: SkillGroupBreakdown
    preferred: SkillGroupBreakdown


def match_passport_to_requirements(
    passport: SkillPassportResponse,
    requirements: list[MatchRequirement] | tuple[MatchRequirement, ...],
) -> MatchResult:
    """Compare a Skill Passport against structured vacancy requirements.

    Score is an integer in ``[0, 100]``:

    - If both required and preferred exist:
      ``round(required_ratio * 70 + preferred_ratio * 30)``
    - If only required exist: ``round(required_ratio * 100)``
    - If only preferred exist: ``round(preferred_ratio * 100)``
    - If no requirements: ``0``

    ``ratio = matched_count / total_count`` for that group. Missing required
    skills therefore lower the score proportionally.
    """
    owned = {skill.id: skill.name for skill in passport.skills}

    required_reqs = [r for r in requirements if r.requirement_type == "required"]
    preferred_reqs = [r for r in requirements if r.requirement_type == "preferred"]

    required = _split_group(owned, required_reqs)
    preferred = _split_group(owned, preferred_reqs)

    score = _compute_score(
        matched_required=len(required.matched),
        total_required=len(required_reqs),
        matched_preferred=len(preferred.matched),
        total_preferred=len(preferred_reqs),
    )
    return MatchResult(score=score, required=required, preferred=preferred)


def _split_group(
    owned: dict[UUID, str], requirements: list[MatchRequirement]
) -> SkillGroupBreakdown:
    matched: list[str] = []
    missing: list[str] = []
    for requirement in requirements:
        if requirement.skill_id in owned:
            matched.append(owned[requirement.skill_id])
        else:
            missing.append(requirement.skill_name)
    return SkillGroupBreakdown(matched=tuple(matched), missing=tuple(missing))


def _compute_score(
    *,
    matched_required: int,
    total_required: int,
    matched_preferred: int,
    total_preferred: int,
) -> int:
    if total_required == 0 and total_preferred == 0:
        return 0

    required_ratio = (
        matched_required / total_required if total_required > 0 else 0.0
    )
    preferred_ratio = (
        matched_preferred / total_preferred if total_preferred > 0 else 0.0
    )

    if total_required == 0:
        return _clamp_score(round(preferred_ratio * 100))
    if total_preferred == 0:
        return _clamp_score(round(required_ratio * 100))
    return _clamp_score(
        round(required_ratio * REQUIRED_WEIGHT + preferred_ratio * PREFERRED_WEIGHT)
    )


def _clamp_score(value: int) -> int:
    return max(0, min(100, value))
