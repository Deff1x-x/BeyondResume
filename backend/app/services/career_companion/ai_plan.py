"""AI enhancement for Career Companion plans (optional layer)."""

from __future__ import annotations

import json
import re
from typing import Any

from app.core.config import settings
from app.services.career_companion.context import CompanionContext
from app.services.career_companion.fallback import DraftAction
from app.services.career_companion.validation import validate_ai_actions


def enhance_plan_with_ai(
    context: CompanionContext,
    fallback_actions: list[DraftAction],
    *,
    revision_hint: str | None = None,
) -> tuple[list[DraftAction], str] | None:
    provider_name = (settings.llm_provider or "mock").lower()

    prompt = _build_prompt(context, fallback_actions, revision_hint=revision_hint)
    raw = _generate(provider_name, prompt, fallback_actions)
    if not raw:
        return None

    try:
        payload = json.loads(_extract_json(raw))
    except (json.JSONDecodeError, TypeError, ValueError):
        return None

    validated = validate_ai_actions(payload, context, fallback_actions)
    if not validated:
        return None

    mode = "mock" if provider_name == "mock" else "live"
    return validated, mode


def answer_chat_with_ai(
    context: CompanionContext,
    actions: list[DraftAction] | list[Any],
    question: str,
) -> str | None:
    provider_name = (settings.llm_provider or "mock").lower()
    if provider_name == "mock":
        return _mock_chat_answer(actions, question)

    # Live path: keep answers grounded by injecting only plan facts
    prompt = (
        "You are BeyondResume Career Companion. Answer ONLY using the plan facts below. "
        "Do not invent projects, skills, percentages, or match scores.\n\n"
        f"QUESTION: {question}\n\n"
        f"PLAN FACTS: {json.dumps(_facts(context, actions), ensure_ascii=True)}"
    )
    try:
        from app.integrations.ai_hiring_intelligence import get_hiring_intelligence_provider

        # Reuse OpenAI-capable provider plumbing when available
        provider = get_hiring_intelligence_provider()
        return provider.generate(prompt).strip() or None
    except Exception:
        return _mock_chat_answer(actions, question)


def _generate(provider_name: str, prompt: str, fallback_actions: list[DraftAction]) -> str:
    if provider_name == "mock":
        return json.dumps(
            {
                "actions": [
                    {
                        "horizon": action.horizon,
                        "action_type": action.action_type,
                        "title": action.title,
                        "description": action.description,
                        "why_it_matters": action.why_it_matters,
                        "implementation_steps": action.implementation_steps,
                        "expected_artifacts": action.expected_artifacts,
                        "verification_method": action.verification_method,
                        "estimated_effort": action.estimated_effort,
                        "project_label": action.project_label,
                        "github_repository_id": str(action.github_repository_id)
                        if action.github_repository_id
                        else None,
                        "gap_skills": [
                            s.skill_name for s in action.skills if s.role == "gap"
                        ],
                        "potential_skills": [
                            s.skill_name for s in action.skills if s.role == "potential_cover"
                        ],
                        "priority_explanation": action.priority_explanation,
                    }
                    for action in fallback_actions
                ]
            }
        )

    try:
        from app.integrations.ai_hiring_intelligence import get_hiring_intelligence_provider

        provider = get_hiring_intelligence_provider()
        return provider.generate(prompt)
    except Exception:
        return ""


def _build_prompt(
    context: CompanionContext,
    fallback_actions: list[DraftAction],
    *,
    revision_hint: str | None,
) -> str:
    return (
        "Generate a Career Companion JSON plan. Use ONLY provided facts. "
        "Prefer improve_existing_project over build_new_project when a project exists. "
        "Never invent repositories, skills, or percentages.\n"
        f"REVISION: {revision_hint or 'none'}\n"
        f"CONTEXT: {json.dumps(_facts(context, fallback_actions), ensure_ascii=True)}\n"
        'Return JSON: {"actions":[{horizon,action_type,title,description,why_it_matters,'
        "implementation_steps,expected_artifacts,verification_method,estimated_effort,"
        "project_label,github_repository_id,gap_skills,potential_skills,priority_explanation}]}"
    )


def _facts(context: CompanionContext, actions: list[Any]) -> dict[str, Any]:
    return {
        "mode": context.mode,
        "target_role": context.target_role,
        "verified_skills": list(context.verified_skill_names),
        "projects": [
            {"id": str(p.id), "label": p.label, "url": p.repository_url}
            for p in context.projects
        ],
        "fallback_titles": [getattr(a, "title", "") for a in actions],
        "directions": list(context.explore_directions),
        "next_level": [item.vacancy.title for item in context.next_level_vacancies[:5]],
    }


def _extract_json(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        return raw[start : end + 1]
    return raw


def _mock_chat_answer(actions: list[Any], question: str) -> str:
    q = question.lower()
    if not actions:
        return (
            "Your current plan has no actions yet. Generate a plan for a vacancy or role first. "
            "I only explain recommendations grounded in your evidence and vacancy gaps."
        )
    top = actions[0]
    title = getattr(top, "title", "the top action")
    why = getattr(top, "why_it_matters", "")
    if "why" in q:
        return f"{title}. {why}"
    if "maximum" in q or "biggest" in q or "important" in q:
        return (
            f"The highest-priority action on your plan is: {title}. "
            f"{getattr(top, 'priority_explanation', '')}"
        )
    if "existing" in q:
        improve = [
            a for a in actions
            if getattr(a, "action_type", "") == "improve_existing_project"
        ]
        if improve:
            return (
                f"Yes — prefer improving {getattr(improve[0], 'project_label', 'an existing project')}: "
                f"{improve[0].title}."
            )
        return "Your current plan does not include an improve-existing-project action."
    if "ready" in q or "отклик" in q:
        return (
            "Readiness depends on required skill gaps and match signals in Current Position. "
            "Complete Fix Now actions and re-sync evidence before treating yourself as ready."
        )
    return (
        f"Based on your plan, start with “{title}”. "
        "I can only reason over your evidence, gaps, and the actions already on this plan."
    )
