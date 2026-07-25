"""Deterministic priority scoring for companion actions."""

from __future__ import annotations

from dataclasses import dataclass

from app.services.career_companion.gaps import SkillGap


@dataclass(frozen=True, slots=True)
class PriorityResult:
    score: float
    explanation: str


def score_action(
    *,
    gaps_covered: list[SkillGap],
    uses_existing_project: bool,
    horizon: str,
    effort: str = "medium",
    growth_vacancy_share: float = 0.0,
) -> PriorityResult:
    score = 0.0
    parts: list[str] = []

    required = [g for g in gaps_covered if g.kind == "required"]
    preferred = [g for g in gaps_covered if g.kind == "preferred"]
    growth = [g for g in gaps_covered if g.kind == "growth"]

    score += 25.0 * len(required)
    if required:
        parts.append(f"Closes {len(required)} required gap(s)")

    score += 10.0 * len(preferred)
    if preferred:
        parts.append(f"Improves {len(preferred)} preferred skill(s)")

    multi = len(gaps_covered)
    if multi >= 2:
        score += 12.0 * (multi - 1)
        parts.append(f"Covers {multi} skills in one action")

    freq = sum(g.vacancy_count for g in gaps_covered)
    score += min(20.0, float(freq) * 2.0)
    if freq:
        parts.append(f"Appears across {freq} relevant vacancy signal(s)")

    if uses_existing_project:
        score += 15.0
        parts.append("Reuses an existing project for faster evidence")
    else:
        score += 4.0
        parts.append("Needs a new project for clean evidence")

    effort_penalty = {"low": 0.0, "medium": 3.0, "high": 8.0}.get(effort, 3.0)
    score -= effort_penalty

    if horizon == "fix_now":
        score += 8.0
    elif horizon == "grow_further":
        score += min(18.0, growth_vacancy_share * 40.0)
        if growth_vacancy_share > 0:
            parts.append(
                f"Appears in about {round(growth_vacancy_share * 100)}% of next-level vacancies analyzed"
            )

    if growth:
        parts.append(f"Supports {len(growth)} next-level skill(s)")

    return PriorityResult(score=round(max(score, 0.0), 2), explanation="; ".join(parts) or "Baseline priority")
