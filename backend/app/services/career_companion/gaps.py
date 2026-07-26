"""Gap and growth analysis for Career Companion."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from uuid import UUID

from app.services.career_companion.context import CompanionContext


@dataclass(frozen=True, slots=True)
class SkillGap:
    skill_name: str
    skill_id: UUID | None
    kind: str  # required | preferred | growth
    vacancy_count: int
    required_count: int
    preferred_count: int
    evidence_state: str


def analyze_gaps(context: CompanionContext) -> tuple[SkillGap, ...]:
    present = {name.strip().lower() for name in context.verified_skill_names}
    gaps: list[SkillGap] = []

    if context.mode == "target_vacancy" and context.target_match is not None:
        match = context.target_match
        for name in match.match.required.missing:
            gaps.append(
                _gap_from_name(context, name, "required", present, vacancy_count=1)
            )
        for name in match.match.preferred.missing:
            gaps.append(
                _gap_from_name(context, name, "preferred", present, vacancy_count=1)
            )
        return tuple(_dedupe(gaps))

    # Role / growth / explore: aggregate frequencies for missing skills
    for freq in context.skill_frequencies:
        if freq.skill_name.strip().lower() in present:
            continue
        kind = "required" if freq.required_count > 0 else "preferred"
        gaps.append(
            SkillGap(
                skill_name=freq.skill_name,
                skill_id=context.verified_skill_ids.get(freq.skill_name.lower()),
                kind=kind,
                vacancy_count=freq.vacancy_count,
                required_count=freq.required_count,
                preferred_count=freq.preferred_count,
                evidence_state="not_found",
            )
        )
    return tuple(_dedupe(gaps))


def analyze_mode_gaps(context: CompanionContext) -> tuple[SkillGap, ...]:
    """Mode-aware gap spine.

    career_growth ranks next-level vacancy skills; every other mode ranks the
    current target. Falls back to current-target gaps when no next-level
    vacancy data exists.
    """
    if context.mode == "career_growth":
        growth = analyze_growth_gaps(context)
        if growth:
            return growth
    return analyze_gaps(context)


def analyze_growth_gaps(context: CompanionContext) -> tuple[SkillGap, ...]:
    present = {name.strip().lower() for name in context.verified_skill_names}
    counter: Counter[str] = Counter()
    required_counter: Counter[str] = Counter()
    display: dict[str, str] = {}

    for item in context.next_level_vacancies:
        for name in item.required_skills:
            key = name.strip().lower()
            counter[key] += 1
            required_counter[key] += 1
            display[key] = name
        for name in item.preferred_skills:
            key = name.strip().lower()
            counter[key] += 1
            display.setdefault(key, name)

    gaps: list[SkillGap] = []
    total = max(len(context.next_level_vacancies), 1)
    for key, count in counter.most_common():
        if key in present:
            continue
        gaps.append(
            SkillGap(
                skill_name=display[key],
                skill_id=None,
                kind="growth",
                vacancy_count=count,
                required_count=required_counter.get(key, 0),
                preferred_count=count - required_counter.get(key, 0),
                evidence_state="not_found",
            )
        )
        if len(gaps) >= 12:
            break
    # Attach frequency percent via vacancy_count / total for callers
    _ = total
    return tuple(gaps)


def build_current_position(context: CompanionContext, gaps: tuple[SkillGap, ...]) -> dict:
    # `growth` gaps come from next-level vacancies and carry their own counts.
    missing_required = [
        g.skill_name
        for g in gaps
        if g.kind == "required" or (g.kind == "growth" and g.required_count > 0)
    ]
    missing_preferred = [
        g.skill_name
        for g in gaps
        if g.kind == "preferred" or (g.kind == "growth" and g.required_count == 0)
    ]
    readiness = "not_ready"
    if context.target_match is not None:
        score = context.target_match.match.score
        if score >= 75 and not missing_required:
            readiness = "ready"
        elif score >= 50:
            readiness = "nearly_ready"
    elif not missing_required and context.verified_skill_names:
        readiness = "nearly_ready"

    strongest = [
        {
            "id": str(project.id),
            "label": project.label,
            "repository_url": project.repository_url,
        }
        for project in context.projects[:5]
    ]

    goal_label = _goal_label(context)

    return {
        "goal_label": goal_label,
        "mode": context.mode,
        "verified_skills": list(context.verified_skill_names),
        "missing_required_skills": missing_required,
        "missing_preferred_skills": missing_preferred,
        "weak_evidence": [
            skill.name
            for skill in context.passport.skills
            if skill.evidence_confidence < 0.45
        ][:8],
        "strongest_projects": strongest,
        "has_resume": context.has_resume,
        "readiness": readiness,
        "target_match_score": context.target_match.match.score if context.target_match else None,
        "explore_directions": list(context.explore_directions),
        "next_level_titles": [
            item.vacancy.title for item in context.next_level_vacancies[:5]
        ],
    }


def _goal_label(context: CompanionContext) -> str:
    """Mode-specific goal so each mode's result is visibly distinct."""
    if context.target_match is not None:
        return (
            f"{context.target_match.vacancy.title} at {context.target_match.company_name}"
        )
    if context.mode == "explore_direction":
        directions = list(context.explore_directions)
        if directions:
            return f"Possible directions: {', '.join(directions[:3])}"
        return "Possible career directions"
    if context.mode == "career_growth":
        next_title = (
            context.next_level_vacancies[0].vacancy.title
            if context.next_level_vacancies
            else None
        )
        if next_title:
            return f"Next level: {next_title}"
        if context.target_role:
            return f"Next level after {context.target_role}"
        return "Next career level"
    return context.target_role or "Career development"


def _gap_from_name(
    context: CompanionContext,
    name: str,
    kind: str,
    present: set[str],
    *,
    vacancy_count: int,
) -> SkillGap:
    key = name.strip().lower()
    freq = next(
        (item for item in context.skill_frequencies if item.skill_name.lower() == key),
        None,
    )
    return SkillGap(
        skill_name=name,
        skill_id=context.verified_skill_ids.get(key),
        kind=kind,
        vacancy_count=freq.vacancy_count if freq else vacancy_count,
        required_count=freq.required_count if freq else (1 if kind == "required" else 0),
        preferred_count=freq.preferred_count if freq else (1 if kind == "preferred" else 0),
        evidence_state="verified" if key in present else "not_found",
    )


def _dedupe(gaps: list[SkillGap]) -> list[SkillGap]:
    seen: set[str] = set()
    result: list[SkillGap] = []
    for gap in gaps:
        key = gap.skill_name.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(gap)
    return result
