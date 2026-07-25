"""Persist and orchestrate Career Companion plans."""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.career_companion_action import CareerCompanionAction
from app.models.career_companion_action_skill import CareerCompanionActionSkill
from app.models.career_companion_plan import CareerCompanionPlan
from app.models.career_companion_progress_event import CareerCompanionProgressEvent
from app.models.skill import Skill
from app.services.career_companion.context import build_companion_context, resolve_skill_id
from app.services.career_companion.fallback import DraftAction, assemble_fallback_actions
from app.services.career_companion.gaps import analyze_gaps, build_current_position


ALLOWED_MANUAL_STATUSES = {"accepted", "in_progress", "awaiting_evidence", "dismissed"}


class CareerCompanionError(Exception):
    def __init__(self, message: str, *, code: str = "CAREER_COMPANION_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


def get_active_plan(session: Session, candidate_id: UUID) -> CareerCompanionPlan | None:
    return session.execute(
        select(CareerCompanionPlan)
        .where(
            CareerCompanionPlan.candidate_id == candidate_id,
            CareerCompanionPlan.status == "active",
        )
        .options(
            selectinload(CareerCompanionPlan.actions).selectinload(CareerCompanionAction.skills),
            selectinload(CareerCompanionPlan.progress_events),
            selectinload(CareerCompanionPlan.chat_messages),
        )
        .order_by(CareerCompanionPlan.updated_at.desc())
    ).scalars().first()


def generate_plan(
    session: Session,
    *,
    candidate_id: UUID,
    mode: str,
    target_vacancy_id: UUID | None = None,
    target_role: str | None = None,
    prefer_ai: bool = True,
    revision_hint: str | None = None,
) -> CareerCompanionPlan:
    if mode == "target_vacancy" and target_vacancy_id is None:
        raise CareerCompanionError(
            "target_vacancy_id is required for target_vacancy mode",
            code="INVALID_COMPANION_TARGET",
        )

    context = build_companion_context(
        session,
        candidate_id=candidate_id,
        mode=mode,
        target_vacancy_id=target_vacancy_id,
        target_role=target_role,
    )
    if mode == "target_vacancy" and context.target_match is None:
        raise CareerCompanionError(
            "Target vacancy was not found or is unavailable",
            code="INVALID_COMPANION_TARGET",
        )

    gaps = analyze_gaps(context)
    position = build_current_position(context, gaps)
    draft_actions = assemble_fallback_actions(context)
    generation_mode = "fallback"

    if prefer_ai:
        try:
            from app.services.career_companion.ai_plan import enhance_plan_with_ai

            enhanced = enhance_plan_with_ai(context, draft_actions, revision_hint=revision_hint)
            if enhanced is not None:
                draft_actions, generation_mode = enhanced
        except Exception:
            generation_mode = "fallback"

    if revision_hint:
        draft_actions = _apply_revision_filters(draft_actions, revision_hint)

    previous = session.execute(
        select(CareerCompanionPlan)
        .where(
            CareerCompanionPlan.candidate_id == candidate_id,
            CareerCompanionPlan.status == "active",
        )
        .options(selectinload(CareerCompanionPlan.actions).selectinload(CareerCompanionAction.skills))
    ).scalars().all()
    preserved_statuses = _collect_preservable_statuses(previous)
    for plan in previous:
        plan.status = "archived"
    session.flush()

    plan = CareerCompanionPlan(
        id=uuid4(),
        candidate_id=candidate_id,
        mode=mode,
        target_vacancy_id=target_vacancy_id,
        target_role=context.target_role,
        status="active",
        generation_mode=generation_mode,
        context_hash=context.context_hash,
        summary={
            "headline": _headline(position, draft_actions),
            "fix_now_count": sum(1 for a in draft_actions if a.horizon == "fix_now"),
            "build_next_count": sum(1 for a in draft_actions if a.horizon == "build_next"),
            "grow_further_count": sum(1 for a in draft_actions if a.horizon == "grow_further"),
            "directions": list(context.explore_directions),
        },
        current_position=position,
    )
    session.add(plan)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        winner = get_active_plan(session, candidate_id)
        if winner is not None:
            return winner
        raise CareerCompanionError(
            "Could not create career companion plan due to a concurrent update",
            code="COMPANION_CONFLICT",
        ) from exc

    for draft in draft_actions:
        _persist_action(session, plan.id, draft, preserved_statuses=preserved_statuses)

    session.add(
        CareerCompanionProgressEvent(
            id=uuid4(),
            plan_id=plan.id,
            event_type="plan_generated",
            title="Career plan generated",
            detail=f"Generated via {generation_mode} for mode {mode}.",
            payload={"generation_mode": generation_mode, "mode": mode},
        )
    )
    session.commit()
    return get_active_plan(session, candidate_id)  # type: ignore[return-value]


def patch_action_status(
    session: Session,
    *,
    candidate_id: UUID,
    action_id: UUID,
    status: str,
) -> CareerCompanionAction:
    if status not in ALLOWED_MANUAL_STATUSES:
        raise CareerCompanionError(
            "Completed status requires evidence verification",
            code="INVALID_ACTION_STATUS",
        )
    action = session.execute(
        select(CareerCompanionAction)
        .join(CareerCompanionPlan)
        .where(
            CareerCompanionAction.id == action_id,
            CareerCompanionPlan.candidate_id == candidate_id,
            CareerCompanionPlan.status == "active",
        )
        .options(selectinload(CareerCompanionAction.skills))
    ).scalar_one_or_none()
    if action is None:
        raise CareerCompanionError("Action not found", code="ACTION_NOT_FOUND")

    action.status = status
    session.add(
        CareerCompanionProgressEvent(
            id=uuid4(),
            plan_id=action.plan_id,
            event_type="action_status_changed",
            title=f"Action marked {status.replace('_', ' ')}",
            detail=action.title,
            payload={"action_id": str(action.id), "status": status},
        )
    )
    session.commit()
    session.refresh(action)
    return action


def _persist_action(
    session: Session,
    plan_id: UUID,
    draft: DraftAction,
    *,
    preserved_statuses: dict[tuple[str, frozenset[str]], str] | None = None,
) -> None:
    status = "suggested"
    if preserved_statuses:
        key = (
            draft.horizon,
            frozenset(skill.skill_name.lower() for skill in draft.skills if skill.role == "gap"),
        )
        status = preserved_statuses.get(key, "suggested")

    action = CareerCompanionAction(
        id=draft.id,
        plan_id=plan_id,
        horizon=draft.horizon,
        action_type=draft.action_type,
        status=status,
        title=draft.title,
        description=draft.description,
        why_it_matters=draft.why_it_matters,
        implementation_steps=draft.implementation_steps,
        expected_artifacts=draft.expected_artifacts,
        verification_method=draft.verification_method,
        estimated_effort=draft.estimated_effort,
        github_repository_id=draft.github_repository_id,
        project_label=draft.project_label,
        current_target_impact=draft.current_target_impact,
        career_growth_impact=draft.career_growth_impact,
        priority_score=draft.priority_score,
        priority_explanation=draft.priority_explanation,
        sort_order=draft.sort_order,
    )
    session.add(action)
    session.flush()

    seen: set[tuple[str, str]] = set()
    for skill in draft.skills:
        key = (skill.skill_name.lower(), skill.role)
        if key in seen:
            continue
        seen.add(key)
        skill_id = skill.skill_id or resolve_skill_id(session, skill.skill_name)
        if skill_id is None:
            row = session.execute(
                select(Skill).where(Skill.canonical_name.ilike(skill.skill_name))
            ).scalars().first()
            if row is None:
                continue
            skill_id = row.id
        session.add(
            CareerCompanionActionSkill(
                id=uuid4(),
                action_id=action.id,
                skill_id=skill_id,
                skill_name=skill.skill_name,
                role=skill.role,
            )
        )


PRESERVABLE_STATUSES = {
    "accepted",
    "in_progress",
    "awaiting_evidence",
    "evidence_detected",
    "partially_verified",
}


def _collect_preservable_statuses(
    previous_plans: list[CareerCompanionPlan],
) -> dict[tuple[str, frozenset[str]], str]:
    """Carry forward in-flight action statuses across regenerate/revision."""
    preserved: dict[tuple[str, frozenset[str]], str] = {}
    for plan in previous_plans:
        for action in plan.actions:
            if action.status not in PRESERVABLE_STATUSES:
                continue
            gaps = frozenset(
                skill.skill_name.lower()
                for skill in action.skills
                if skill.role == "gap"
            )
            key = (action.horizon, gaps)
            # Prefer the most advanced status if duplicates collide.
            existing = preserved.get(key)
            if existing is None or _status_rank(action.status) >= _status_rank(existing):
                preserved[key] = action.status
    return preserved


def _status_rank(status: str) -> int:
    order = [
        "suggested",
        "accepted",
        "in_progress",
        "awaiting_evidence",
        "evidence_detected",
        "partially_verified",
        "completed",
    ]
    try:
        return order.index(status)
    except ValueError:
        return -1


def _headline(position: dict, actions: list[DraftAction]) -> str:
    missing = position.get("missing_required_skills") or []
    if missing and actions:
        top = actions[0]
        return (
            f"You are missing {', '.join(missing[:3])} for your current target. "
            f"Highest-leverage next step: {top.title}."
        )
    if actions:
        return f"Start with: {actions[0].title}."
    return "Your evidence profile already covers the current target signals."


def _apply_revision_filters(actions: list[DraftAction], hint: str) -> list[DraftAction]:
    text = hint.lower()
    result = list(actions)
    if "existing project" in text or "no new project" in text or "only existing" in text:
        filtered = [a for a in result if a.action_type != "build_new_project"]
        if filtered:
            result = filtered
    if "two week" in text or "2 week" in text or "shorter" in text:
        result = result[:2]
    if "hours" in text:
        result = [a for a in result if a.estimated_effort != "high"] or result[:2]
    for index, action in enumerate(result):
        action.sort_order = index
    return result
