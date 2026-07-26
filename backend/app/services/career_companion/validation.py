"""Semantic validation for AI-generated companion actions."""

from __future__ import annotations

import re
from typing import Any
from uuid import uuid4

from app.services.career_companion.context import CompanionContext
from app.services.career_companion.fallback import DraftAction, DraftActionSkill
from app.services.career_companion.gaps import SkillGap
from app.services.career_companion.priority import score_action

ALLOWED_HORIZONS = {"fix_now", "build_next", "grow_further"}
ALLOWED_TYPES = {
    "improve_existing_project",
    "build_new_project",
    "learn_foundation",
}
MAX_ACTIONS = 9
# AI must never supply these as authoritative numeric facts.
FORBIDDEN_FACT_KEYS = {
    "match_score",
    "match_delta",
    "score",
    "readiness_score",
    "priority_score",
    "status",
    "completed",
}


def validate_ai_actions(
    payload: dict[str, Any],
    context: CompanionContext,
    fallback: list[DraftAction],
) -> list[DraftAction] | None:
    raw_actions = payload.get("actions")
    if not isinstance(raw_actions, list) or not raw_actions:
        return None

    project_ids = {str(p.id): p for p in context.projects}
    project_labels = {p.label.lower(): p for p in context.projects}
    known_skills = {name.lower() for name in context.verified_skill_names}
    # Also allow gap skills already present in deterministic fallback.
    for action in fallback:
        for skill in action.skills:
            known_skills.add(skill.skill_name.lower())
    freq_names = {f.skill_name.lower() for f in context.skill_frequencies}
    allow_skills = known_skills | freq_names

    validated: list[DraftAction] = []
    for index, item in enumerate(raw_actions[:MAX_ACTIONS]):
        if not isinstance(item, dict):
            continue
        # Ignore any attempt to override deterministic facts.
        if any(key in item for key in FORBIDDEN_FACT_KEYS):
            # Strip and continue — do not reject whole plan for extra fields.
            item = {
                key: value
                for key, value in item.items()
                if key not in FORBIDDEN_FACT_KEYS
            }

        horizon = str(item.get("horizon") or "")
        action_type = str(item.get("action_type") or "")
        title = str(item.get("title") or "").strip()
        if horizon not in ALLOWED_HORIZONS or action_type not in ALLOWED_TYPES or not title:
            continue

        repo_id_raw = item.get("github_repository_id")
        project_label = item.get("project_label")
        github_repository_id = None
        label = None
        if repo_id_raw:
            project = project_ids.get(str(repo_id_raw))
            if project is None:
                continue  # hallucinated repo
            github_repository_id = project.id
            label = project.label
        elif project_label:
            project = project_labels.get(str(project_label).lower())
            if project is None and action_type == "improve_existing_project":
                continue
            if project is not None:
                github_repository_id = project.id
                label = project.label

        if action_type == "improve_existing_project" and github_repository_id is None:
            continue

        gap_skills = [
            str(name).strip()
            for name in (item.get("gap_skills") or [])
            if str(name).strip() and str(name).strip().lower() in allow_skills
        ]
        potential = [
            str(name).strip()
            for name in (item.get("potential_skills") or gap_skills)
            if str(name).strip() and str(name).strip().lower() in allow_skills
        ]
        if not gap_skills:
            continue

        gaps = [
            SkillGap(
                skill_name=name,
                skill_id=context.verified_skill_ids.get(name.lower()),
                kind="required",
                vacancy_count=next(
                    (
                        freq.vacancy_count
                        for freq in context.skill_frequencies
                        if freq.skill_name.lower() == name.lower()
                    ),
                    1,
                ),
                required_count=1,
                preferred_count=0,
                evidence_state="not_found",
            )
            for name in gap_skills
        ]
        pr = score_action(
            gaps_covered=gaps,
            uses_existing_project=action_type == "improve_existing_project",
            horizon=horizon,
            effort=str(item.get("estimated_effort") or "medium"),
        )

        steps = item.get("implementation_steps") or []
        artifacts = item.get("expected_artifacts") or []
        if not isinstance(steps, list) or not isinstance(artifacts, list):
            continue

        explanation = _strip_invented_percentages(
            str(item.get("priority_explanation") or pr.explanation)
        )

        validated.append(
            DraftAction(
                id=uuid4(),
                horizon=horizon,
                action_type=action_type,
                title=title[:255],
                description=str(item.get("description") or "")[:4000],
                why_it_matters=str(item.get("why_it_matters") or "")[:4000],
                implementation_steps=[str(s) for s in steps][:12],
                expected_artifacts=[str(a) for a in artifacts][:12],
                verification_method=str(
                    item.get("verification_method")
                    or "Re-sync GitHub; skills confirmed only when evidence is detected."
                ),
                estimated_effort=str(item.get("estimated_effort") or "medium")[:40],
                github_repository_id=github_repository_id,
                project_label=label,
                current_target_impact={
                    "closes_required_gaps": len(gap_skills),
                    "skills": gap_skills,
                    "summary": f"Targets {len(gap_skills)} skill gap(s).",
                },
                career_growth_impact={},
                priority_score=pr.score,
                priority_explanation=explanation[:2000],
                sort_order=index,
                skills=[
                    DraftActionSkill(None, name, "gap") for name in gap_skills
                ]
                + [
                    DraftActionSkill(None, name, "potential_cover") for name in potential
                ],
            )
        )

    if not validated:
        return None
    validated.sort(key=lambda item: (-item.priority_score, item.sort_order))
    for index, action in enumerate(validated):
        action.sort_order = index
    return validated


def _strip_invented_percentages(text: str) -> str:
    """Remove match-like percentage claims AI may invent in free text."""
    cleaned = re.sub(r"\b\d{1,3}\s*%\b", "[score omitted]", text)
    cleaned = re.sub(
        r"\bmatch(?:\s+score)?\s*(?:of|=|:)?\s*\d{1,3}\b",
        "match score omitted",
        cleaned,
        flags=re.IGNORECASE,
    )
    return cleaned
