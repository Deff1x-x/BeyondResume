"""Deterministic fallback plan assembler (works without AI)."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from app.services.career_companion.context import CompanionContext, ProjectContext
from app.services.career_companion.gaps import SkillGap, analyze_gaps, analyze_growth_gaps
from app.services.career_companion.priority import score_action


@dataclass
class DraftActionSkill:
    skill_id: UUID | None
    skill_name: str
    role: str


@dataclass
class DraftAction:
    id: UUID
    horizon: str
    action_type: str
    title: str
    description: str
    why_it_matters: str
    implementation_steps: list[str]
    expected_artifacts: list[str]
    verification_method: str
    estimated_effort: str
    github_repository_id: UUID | None
    project_label: str | None
    current_target_impact: dict
    career_growth_impact: dict
    priority_score: float
    priority_explanation: str
    sort_order: int
    skills: list[DraftActionSkill] = field(default_factory=list)


def assemble_fallback_actions(context: CompanionContext) -> list[DraftAction]:
    gaps = analyze_gaps(context)
    growth_gaps = analyze_growth_gaps(context)
    actions: list[DraftAction] = []

    # Fix Now — one critical gap action (prefer improve existing)
    critical = [g for g in gaps if g.kind == "required"][:4]
    if not critical:
        critical = list(gaps[:3])

    if critical:
        project = _best_project(context.projects)
        primary = critical[0]
        related = critical[:3]
        if project is not None:
            actions.append(
                _improve_action(
                    context,
                    horizon="fix_now",
                    project=project,
                    gaps=related,
                    title=f"Add {primary.skill_name} evidence to {project.label}",
                )
            )
        else:
            actions.append(
                _learn_or_build(
                    context,
                    horizon="fix_now",
                    gaps=related,
                    title=f"Create evidence for {primary.skill_name}",
                    prefer_build=True,
                )
            )

    # Build Next — multi-gap project
    multi = list(gaps[:5])
    if len(multi) >= 2:
        project = _best_project(context.projects)
        skill_names = ", ".join(g.skill_name for g in multi[:4])
        if project is not None:
            actions.append(
                _improve_action(
                    context,
                    horizon="build_next",
                    project=project,
                    gaps=multi,
                    title=f"Upgrade {project.label} to cover {skill_names}",
                )
            )
        else:
            role = context.target_role or "Backend"
            actions.append(
                _learn_or_build(
                    context,
                    horizon="build_next",
                    gaps=multi,
                    title=f"Build a production-ready {role} project covering {skill_names}",
                    prefer_build=True,
                )
            )
    elif multi:
        # Single remaining gap as learn foundation
        actions.append(
            _learn_or_build(
                context,
                horizon="build_next",
                gaps=multi,
                title=f"Strengthen foundation in {multi[0].skill_name}",
                prefer_build=False,
            )
        )

    # Grow Further
    if context.mode in {"career_growth", "explore_direction", "target_role"} or growth_gaps:
        grow = list(growth_gaps[:5]) or list(gaps[3:6])
        if grow:
            total_next = max(len(context.next_level_vacancies), 1)
            share = grow[0].vacancy_count / total_next
            project = _best_project(context.projects)
            names = ", ".join(g.skill_name for g in grow[:3])
            next_title = (
                context.next_level_vacancies[0].vacancy.title
                if context.next_level_vacancies
                else "next-level roles"
            )
            if project is not None and len(grow) <= 2:
                action = _improve_action(
                    context,
                    horizon="grow_further",
                    project=project,
                    gaps=grow,
                    title=f"Extend {project.label} toward {next_title}",
                )
            else:
                action = _learn_or_build(
                    context,
                    horizon="grow_further",
                    gaps=grow,
                    title=f"Build an advanced project for {names}",
                    prefer_build=True,
                )
            action.career_growth_impact = {
                "next_level_vacancy_share": round(share, 3),
                "skill": grow[0].skill_name,
                "appears_in_next_level_count": grow[0].vacancy_count,
                "next_level_analyzed": total_next,
                "summary": (
                    f"{grow[0].skill_name} appears in {grow[0].vacancy_count} of "
                    f"{total_next} analyzed next-level vacancies"
                ),
            }
            pr = score_action(
                gaps_covered=grow,
                uses_existing_project=action.action_type == "improve_existing_project",
                horizon="grow_further",
                effort=action.estimated_effort,
                growth_vacancy_share=share,
            )
            action.priority_score = pr.score
            action.priority_explanation = pr.explanation
            actions.append(action)

    # Sort and assign order
    actions.sort(key=lambda item: (-item.priority_score, item.horizon, item.title))
    for index, action in enumerate(actions):
        action.sort_order = index
    return actions


def _best_project(projects: tuple[ProjectContext, ...]) -> ProjectContext | None:
    return projects[0] if projects else None


def _improve_action(
    context: CompanionContext,
    *,
    horizon: str,
    project: ProjectContext,
    gaps: list[SkillGap],
    title: str,
) -> DraftAction:
    skill_names = [g.skill_name for g in gaps]
    pr = score_action(
        gaps_covered=gaps,
        uses_existing_project=True,
        horizon=horizon,
        effort="medium",
    )
    artifacts = _artifacts_for_skills(skill_names)
    return DraftAction(
        id=uuid4(),
        horizon=horizon,
        action_type="improve_existing_project",
        title=title,
        description=(
            f"Improve {project.label} so it produces verifiable evidence for: "
            f"{', '.join(skill_names)}."
        ),
        why_it_matters=(
            f"{project.label} is already in your profile. Extending it creates real evidence "
            "instead of resume-only claims."
        ),
        implementation_steps=_steps_for_improve(project.label, skill_names),
        expected_artifacts=artifacts,
        verification_method=(
            "Re-sync GitHub after pushing changes. Skills are confirmed only if supporting "
            "evidence is detected."
        ),
        estimated_effort="medium",
        github_repository_id=project.id,
        project_label=project.label,
        current_target_impact={
            "closes_required_gaps": sum(1 for g in gaps if g.kind == "required"),
            "closes_preferred_gaps": sum(1 for g in gaps if g.kind == "preferred"),
            "skills": skill_names,
            "summary": f"Closes {sum(1 for g in gaps if g.kind == 'required')} required skill gap(s).",
        },
        career_growth_impact={},
        priority_score=pr.score,
        priority_explanation=pr.explanation,
        sort_order=0,
        skills=[
            DraftActionSkill(skill_id=g.skill_id, skill_name=g.skill_name, role="gap")
            for g in gaps
        ]
        + [
            DraftActionSkill(skill_id=g.skill_id, skill_name=g.skill_name, role="potential_cover")
            for g in gaps
        ],
    )


def _learn_or_build(
    context: CompanionContext,
    *,
    horizon: str,
    gaps: list[SkillGap],
    title: str,
    prefer_build: bool,
) -> DraftAction:
    skill_names = [g.skill_name for g in gaps]
    action_type = "build_new_project" if prefer_build or len(gaps) >= 2 else "learn_foundation"
    pr = score_action(
        gaps_covered=gaps,
        uses_existing_project=False,
        horizon=horizon,
        effort="high" if action_type == "build_new_project" else "medium",
    )
    return DraftAction(
        id=uuid4(),
        horizon=horizon,
        action_type=action_type,
        title=title,
        description=(
            "Create structured evidence for missing skills through a focused project "
            f"covering {', '.join(skill_names)}."
            if action_type == "build_new_project"
            else f"Build foundational understanding and a small demo for {skill_names[0]}."
        ),
        why_it_matters=(
            "No existing project can efficiently absorb these gaps, so a dedicated project "
            "keeps evidence clean and reviewable."
            if action_type == "build_new_project"
            else "A focused foundation step reduces risk before larger project work."
        ),
        implementation_steps=_steps_for_build(skill_names),
        expected_artifacts=_artifacts_for_skills(skill_names),
        verification_method=(
            "Push the project to GitHub and re-sync. Potentially covered skills stay unverified "
            "until evidence is detected."
        ),
        estimated_effort="high" if action_type == "build_new_project" else "medium",
        github_repository_id=None,
        project_label=None,
        current_target_impact={
            "closes_required_gaps": sum(1 for g in gaps if g.kind == "required"),
            "closes_preferred_gaps": sum(1 for g in gaps if g.kind == "preferred"),
            "skills": skill_names,
            "summary": f"Targets {len(skill_names)} skill gap(s) for your current goal.",
        },
        career_growth_impact={},
        priority_score=pr.score,
        priority_explanation=pr.explanation,
        sort_order=0,
        skills=[
            DraftActionSkill(skill_id=g.skill_id, skill_name=g.skill_name, role="gap")
            for g in gaps
        ]
        + [
            DraftActionSkill(skill_id=g.skill_id, skill_name=g.skill_name, role="potential_cover")
            for g in gaps
        ],
    )


def _artifacts_for_skills(skills: list[str]) -> list[str]:
    artifacts = ["README with setup instructions", "Committed source on GitHub"]
    joined = " ".join(skills).lower()
    if "docker" in joined:
        artifacts.extend(["Dockerfile", "docker-compose.yml"])
    if "test" in joined:
        artifacts.append("Automated test suite")
    if "ci" in joined or "github actions" in joined:
        artifacts.append("GitHub Actions workflow")
    if "postgres" in joined or "sql" in joined:
        artifacts.append("Database migrations")
    if "auth" in joined or "jwt" in joined:
        artifacts.append("Authentication endpoints")
    return artifacts


def _steps_for_improve(project: str, skills: list[str]) -> list[str]:
    steps = [f"Review current architecture of {project}"]
    for skill in skills[:4]:
        steps.append(f"Add concrete {skill} support with production-like configuration")
    steps.append("Document how to run and verify locally")
    steps.append("Push changes and re-sync GitHub in BeyondResume")
    return steps


def _steps_for_build(skills: list[str]) -> list[str]:
    return [
        "Define a small but realistic problem statement",
        f"Implement core features covering {', '.join(skills[:4])}",
        "Add tests and operational basics where relevant",
        "Publish to GitHub with clear README",
        "Re-sync GitHub so BeyondResume can detect evidence",
    ]
