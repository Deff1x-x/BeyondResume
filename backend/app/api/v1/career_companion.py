from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_candidate
from app.db.session import get_db
from app.models.job import JobStatus
from app.models.user import User
from app.schemas.career_companion import (
    CareerCompanionActionResponse,
    CareerCompanionActionStatusPatch,
    CareerCompanionChatRequest,
    CareerCompanionChatResponse,
    CareerCompanionGenerateRequest,
    CareerCompanionPlanResponse,
)
from app.services.candidate import get_candidate_profile
from app.services.career_companion import (
    CareerCompanionError,
    generate_plan,
    get_active_plan,
    handle_chat,
    patch_action_status,
    refresh_plan_from_evidence,
)
from app.services.career_companion.context import build_companion_context
from app.services.career_companion_jobs import (
    context_is_large,
    enqueue_async_regenerate_if_large,
    run_roadmap_generation_job_task,
)

router = APIRouter(prefix="/candidate/career-companion", tags=["career-companion"])


def _profile_id(session: Session, user: User) -> UUID:
    profile = get_candidate_profile(session, user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CANDIDATE_PROFILE_REQUIRED", "message": "Candidate profile required"},
        )
    return profile.id


def _http_error(exc: CareerCompanionError) -> HTTPException:
    code = status.HTTP_400_BAD_REQUEST
    if exc.code in {"ACTION_NOT_FOUND", "PLAN_REQUIRED"}:
        code = status.HTTP_404_NOT_FOUND
    if exc.code == "COMPANION_CONFLICT":
        code = status.HTTP_409_CONFLICT
    return HTTPException(
        status_code=code,
        detail={"code": exc.code, "message": exc.message},
    )


@router.get("", response_model=CareerCompanionPlanResponse)
def get_career_companion_plan(
    current_user: Annotated[User, Depends(require_candidate)],
    session: Annotated[Session, Depends(get_db)],
) -> CareerCompanionPlanResponse:
    candidate_id = _profile_id(session, current_user)
    plan = get_active_plan(session, candidate_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "CAREER_COMPANION_NOT_FOUND",
                "message": "No active career companion plan. Generate one first.",
            },
        )
    return CareerCompanionPlanResponse.model_validate(plan)


@router.post("/generate", response_model=CareerCompanionPlanResponse)
def generate_career_companion_plan(
    payload: CareerCompanionGenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(require_candidate)],
    session: Annotated[Session, Depends(get_db)],
) -> CareerCompanionPlanResponse:
    candidate_id = _profile_id(session, current_user)
    context = build_companion_context(
        session,
        candidate_id=candidate_id,
        mode=payload.mode,
        target_vacancy_id=payload.target_vacancy_id,
        target_role=payload.target_role,
    )
    large_context = context_is_large(
        project_count=len(context.projects),
        vacancy_count=len(context.vacancy_matches),
    )
    try:
        # Large contexts: return deterministic fallback immediately; AI runs once async.
        # Small contexts: enhance synchronously.
        plan = generate_plan(
            session,
            candidate_id=candidate_id,
            mode=payload.mode,
            target_vacancy_id=payload.target_vacancy_id,
            target_role=payload.target_role,
            prefer_ai=not large_context,
        )
    except CareerCompanionError as exc:
        raise _http_error(exc) from exc

    if large_context:
        try:
            job = enqueue_async_regenerate_if_large(
                session,
                candidate_id=candidate_id,
                project_count=len(context.projects),
                vacancy_count=len(context.vacancy_matches),
            )
            if job is not None and job.status == JobStatus.PENDING:
                background_tasks.add_task(run_roadmap_generation_job_task, job.id)
        except Exception:
            # Plan already committed — enqueue failure must not become HTTP 500.
            import logging

            logging.getLogger(__name__).exception(
                "Failed to enqueue async Career Companion regeneration"
            )

    refreshed = get_active_plan(session, candidate_id) or plan
    return CareerCompanionPlanResponse.model_validate(refreshed)


@router.patch("/actions/{action_id}", response_model=CareerCompanionActionResponse)
def patch_career_companion_action(
    action_id: UUID,
    payload: CareerCompanionActionStatusPatch,
    current_user: Annotated[User, Depends(require_candidate)],
    session: Annotated[Session, Depends(get_db)],
) -> CareerCompanionActionResponse:
    candidate_id = _profile_id(session, current_user)
    try:
        action = patch_action_status(
            session,
            candidate_id=candidate_id,
            action_id=action_id,
            status=payload.status,
        )
    except CareerCompanionError as exc:
        raise _http_error(exc) from exc
    return CareerCompanionActionResponse.model_validate(action)


@router.post("/chat", response_model=CareerCompanionChatResponse)
def career_companion_chat(
    payload: CareerCompanionChatRequest,
    current_user: Annotated[User, Depends(require_candidate)],
    session: Annotated[Session, Depends(get_db)],
) -> CareerCompanionChatResponse:
    candidate_id = _profile_id(session, current_user)
    try:
        return handle_chat(session, candidate_id=candidate_id, message=payload.message)
    except CareerCompanionError as exc:
        raise _http_error(exc) from exc


@router.post("/refresh-from-evidence", response_model=CareerCompanionPlanResponse)
def refresh_career_companion_from_evidence(
    current_user: Annotated[User, Depends(require_candidate)],
    session: Annotated[Session, Depends(get_db)],
) -> CareerCompanionPlanResponse:
    candidate_id = _profile_id(session, current_user)
    plan = refresh_plan_from_evidence(session, candidate_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "CAREER_COMPANION_NOT_FOUND",
                "message": "No active career companion plan.",
            },
        )
    return CareerCompanionPlanResponse.model_validate(plan)
