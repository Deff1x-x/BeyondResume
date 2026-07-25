"""Plan-bound chat and light revision requests."""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.models.career_companion_chat_message import CareerCompanionChatMessage
from app.schemas.career_companion import CareerCompanionChatResponse, CareerCompanionPlanResponse
from app.services.career_companion.ai_plan import answer_chat_with_ai
from app.services.career_companion.context import build_companion_context
from app.services.career_companion.fallback import DraftAction
from app.services.career_companion.plan_service import (
    CareerCompanionError,
    generate_plan,
    get_active_plan,
)


REVISION_HINTS = (
    "shorter",
    "two week",
    "2 week",
    "existing project",
    "only existing",
    "no new project",
    "hours",
    "focus on one vacancy",
    "next level",
    "middle",
)


def handle_chat(
    session: Session,
    *,
    candidate_id: UUID,
    message: str,
) -> CareerCompanionChatResponse:
    plan = get_active_plan(session, candidate_id)
    if plan is None:
        raise CareerCompanionError("Generate a plan before chatting", code="PLAN_REQUIRED")

    session.add(
        CareerCompanionChatMessage(
            id=uuid4(),
            plan_id=plan.id,
            role="user",
            content=message.strip(),
        )
    )
    session.flush()

    revision = _detect_revision(message)
    updated_plan = None
    if revision:
        updated_plan = generate_plan(
            session,
            candidate_id=candidate_id,
            mode=plan.mode,
            target_vacancy_id=plan.target_vacancy_id,
            target_role=plan.target_role,
            prefer_ai=True,
            revision_hint=message,
        )
        plan = updated_plan or plan

    context = build_companion_context(
        session,
        candidate_id=candidate_id,
        mode=plan.mode,
        target_vacancy_id=plan.target_vacancy_id,
        target_role=plan.target_role,
    )
    draft_like = [
        DraftAction(
            id=action.id,
            horizon=action.horizon,
            action_type=action.action_type,
            title=action.title,
            description=action.description,
            why_it_matters=action.why_it_matters,
            implementation_steps=list(action.implementation_steps or []),
            expected_artifacts=list(action.expected_artifacts or []),
            verification_method=action.verification_method,
            estimated_effort=action.estimated_effort,
            github_repository_id=action.github_repository_id,
            project_label=action.project_label,
            current_target_impact=dict(action.current_target_impact or {}),
            career_growth_impact=dict(action.career_growth_impact or {}),
            priority_score=action.priority_score,
            priority_explanation=action.priority_explanation,
            sort_order=action.sort_order,
            skills=[],
        )
        for action in plan.actions
    ]
    answer = answer_chat_with_ai(context, draft_like, message) or (
        "I can only answer using your current Career Companion plan and evidence context."
    )
    if revision:
        answer = (
            f"Updated your plan based on: “{message.strip()}”.\n\n{answer}"
        )

    assistant = CareerCompanionChatMessage(
        id=uuid4(),
        plan_id=plan.id,
        role="assistant",
        content=answer,
        revision_applied=revision,
    )
    session.add(assistant)
    session.commit()
    session.refresh(assistant)

    fresh = get_active_plan(session, candidate_id)
    return CareerCompanionChatResponse(
        message=assistant,  # type: ignore[arg-type]
        plan=CareerCompanionPlanResponse.model_validate(fresh) if fresh else None,
    )


def _detect_revision(message: str) -> str | None:
    text = message.lower()
    for hint in REVISION_HINTS:
        if hint in text:
            return hint
    if "пересмотр" in text or "короче" in text or "только существующ" in text:
        return "revision"
    return None
