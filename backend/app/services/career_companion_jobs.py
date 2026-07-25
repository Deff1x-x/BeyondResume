"""Background Career Companion regenerate jobs (roadmap_generation type)."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.job import Job, JobType
from app.services.career_companion.context import build_companion_context
from app.services.career_companion.plan_service import generate_plan, get_active_plan
from app.services.jobs import (
    JobTransitionError,
    SubjectJobRequestResult,
    claim_job,
    complete_running_job,
    fail_running_job,
    get_or_create_active_subject_job,
)

ROADMAP_GENERATION_SUBJECT_TYPE = "career_companion_candidate"
LARGE_CONTEXT_PROJECT_THRESHOLD = 8
LARGE_CONTEXT_VACANCY_THRESHOLD = 12

logger = logging.getLogger(__name__)


def context_is_large(*, project_count: int, vacancy_count: int) -> bool:
    return (
        project_count >= LARGE_CONTEXT_PROJECT_THRESHOLD
        or vacancy_count >= LARGE_CONTEXT_VACANCY_THRESHOLD
    )


def request_roadmap_generation(
    session: Session, *, candidate_id: UUID
) -> SubjectJobRequestResult:
    return get_or_create_active_subject_job(
        session,
        job_type=JobType.ROADMAP_GENERATION,
        candidate_id=candidate_id,
        subject_type=ROADMAP_GENERATION_SUBJECT_TYPE,
        subject_id=candidate_id,
    )


def run_roadmap_generation_job(session: Session, job_id: UUID) -> Job:
    job = claim_job(session, job_id)
    if job.job_type != JobType.ROADMAP_GENERATION or job.candidate_id is None:
        raise JobTransitionError("Job is not a roadmap generation job")

    try:
        plan = get_active_plan(session, job.candidate_id)
        if plan is None:
            generate_plan(
                session,
                candidate_id=job.candidate_id,
                mode="target_role",
                prefer_ai=True,
            )
        else:
            context = build_companion_context(
                session,
                candidate_id=job.candidate_id,
                mode=plan.mode,
                target_vacancy_id=plan.target_vacancy_id,
                target_role=plan.target_role,
            )
            # Skip stale overwrite: if a newer AI plan already matches current context, no-op.
            if (
                plan.generation_mode in {"live", "mock"}
                and plan.context_hash == context.context_hash
            ):
                return complete_running_job(session, job)

            generate_plan(
                session,
                candidate_id=job.candidate_id,
                mode=plan.mode,
                target_vacancy_id=plan.target_vacancy_id,
                target_role=plan.target_role,
                prefer_ai=True,
            )
    except SQLAlchemyError:
        logger.exception("Roadmap generation job %s failed", job_id)
        session.rollback()
        return fail_running_job(
            session, job, "DATABASE_ERROR", "Career Companion regeneration failed"
        )
    except Exception:
        logger.exception("Roadmap generation job %s failed unexpectedly", job_id)
        session.rollback()
        return fail_running_job(
            session,
            job,
            "ROADMAP_GENERATION_ERROR",
            "Career Companion regeneration failed",
        )

    return complete_running_job(session, job)


def run_roadmap_generation_job_task(job_id: UUID) -> None:
    session = SessionLocal()
    try:
        run_roadmap_generation_job(session, job_id)
    finally:
        session.close()


def enqueue_async_regenerate_if_large(
    session: Session,
    *,
    candidate_id: UUID,
    project_count: int,
    vacancy_count: int,
) -> Job | None:
    """Create a pending roadmap_generation job when the companion context is large."""
    if not context_is_large(project_count=project_count, vacancy_count=vacancy_count):
        return None
    result = request_roadmap_generation(session, candidate_id=candidate_id)
    return result.job
