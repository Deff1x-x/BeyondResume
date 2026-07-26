"""Mode branching for Career Companion goal modes.

Guards that career_growth and explore_direction produce different, evidence-driven
plans instead of collapsing into target_role.
"""

from types import SimpleNamespace
from uuid import uuid4

from app.schemas.skill_passport import SkillPassportResponse
from app.services.career_companion.context import CompanionContext, SkillFrequency
from app.services.career_companion.fallback import assemble_fallback_actions
from app.services.career_companion.gaps import (
    analyze_gaps,
    analyze_mode_gaps,
    build_current_position,
)


def _vacancy_match(title: str, required: list[str], preferred: list[str] | None = None):
    preferred = preferred or []
    return SimpleNamespace(
        vacancy=SimpleNamespace(id=uuid4(), title=title),
        company_name="Acme",
        required_skills=required,
        preferred_skills=preferred,
        match=SimpleNamespace(
            score=40,
            required=SimpleNamespace(matched=[], missing=required),
            preferred=SimpleNamespace(matched=[], missing=preferred),
        ),
    )


def _context(
    mode: str,
    *,
    target_role: str | None = "Backend Developer",
    next_level: tuple = (),
    frequencies: tuple = (),
    directions: tuple = ("Backend", "DevOps"),
):
    return CompanionContext(
        candidate_id=uuid4(),
        mode=mode,
        target_vacancy_id=None,
        target_role=target_role,
        passport=SkillPassportResponse(skills=[], total_skills=0, total_evidence=0),
        verified_skill_names=("Python",),
        verified_skill_ids={},
        projects=(),
        has_resume=True,
        vacancy_matches=next_level,
        target_match=None,
        skill_frequencies=frequencies,
        next_level_vacancies=next_level,
        context_hash="hash",
        explore_directions=directions,
    )


def _frequency(name: str, required: int = 1) -> SkillFrequency:
    return SkillFrequency(
        skill_id=uuid4(),
        skill_name=name,
        vacancy_count=1,
        required_count=required,
        preferred_count=0 if required else 1,
    )


def test_career_growth_uses_next_level_gaps_not_current_target() -> None:
    next_level = (_vacancy_match("Senior Backend Engineer", ["Kubernetes", "Kafka"]),)
    context = _context(
        "career_growth",
        next_level=next_level,
        frequencies=(_frequency("Docker"),),
    )

    current_target = {gap.skill_name for gap in analyze_gaps(context)}
    growth = analyze_mode_gaps(context)
    growth_names = {gap.skill_name for gap in growth}

    assert current_target == {"Docker"}
    assert growth_names == {"Kubernetes", "Kafka"}
    assert all(gap.kind == "growth" for gap in growth)


def test_career_growth_falls_back_to_current_target_without_next_level() -> None:
    context = _context("career_growth", frequencies=(_frequency("Docker"),))
    gaps = analyze_mode_gaps(context)
    assert {gap.skill_name for gap in gaps} == {"Docker"}


def test_growth_gaps_surface_in_current_position() -> None:
    next_level = (_vacancy_match("Senior Backend Engineer", ["Kubernetes"], ["Kafka"]),)
    context = _context("career_growth", next_level=next_level)

    position = build_current_position(context, analyze_mode_gaps(context))

    assert "Kubernetes" in position["missing_required_skills"]
    assert "Kafka" in position["missing_preferred_skills"]


def test_goal_label_is_mode_specific() -> None:
    next_level = (_vacancy_match("Senior Backend Engineer", ["Kubernetes"]),)

    role_position = build_current_position(
        _context("target_role"), analyze_mode_gaps(_context("target_role"))
    )
    growth_context = _context("career_growth", next_level=next_level)
    growth_position = build_current_position(
        growth_context, analyze_mode_gaps(growth_context)
    )
    explore_context = _context("explore_direction", target_role=None)
    explore_position = build_current_position(
        explore_context, analyze_mode_gaps(explore_context)
    )

    assert role_position["goal_label"] == "Backend Developer"
    assert growth_position["goal_label"] == "Next level: Senior Backend Engineer"
    assert explore_position["goal_label"] == "Possible directions: Backend, DevOps"
    assert len({
        role_position["goal_label"],
        growth_position["goal_label"],
        explore_position["goal_label"],
    }) == 3


def test_explore_direction_projects_target_the_strongest_direction() -> None:
    context = _context(
        "explore_direction",
        target_role=None,
        frequencies=(_frequency("Docker"), _frequency("Terraform")),
        directions=("DevOps", "Backend"),
    )

    actions = assemble_fallback_actions(context)
    titles = " ".join(action.title for action in actions)

    assert actions
    assert "DevOps" in titles


def test_career_growth_actions_reference_next_level_target() -> None:
    next_level = (
        _vacancy_match("Senior Backend Engineer", ["Kubernetes", "Kafka", "Terraform"]),
    )
    context = _context("career_growth", next_level=next_level)

    actions = assemble_fallback_actions(context)
    titles = " ".join(action.title for action in actions)

    assert actions
    assert "Kubernetes" in titles or "Senior Backend Engineer" in titles
