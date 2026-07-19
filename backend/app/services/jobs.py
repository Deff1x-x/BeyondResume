"""Type-agnostic Job engine primitives shared by every long-running operation.

Entity-coupled transitions (for example resume_parse, which atomically updates
Resume state) live next to their domain services and reuse these primitives.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.job import Job, JobStatus, JobType


class JobNotFoundError(Exception):
    """The requested job does not exist."""


class JobTransitionError(Exception):
    """The requested job lifecycle transition is not allowed."""


@dataclass(frozen=True, slots=True)
class SubjectJobRequestResult:
    """The active subject Job and whether this request created it."""

    job: Job
    created: bool


def claim_job(session: Session, job_id: UUID) -> Job:
    result = cast(
        CursorResult[object],
        session.execute(
            update(Job)
            .where(Job.id == job_id, Job.status == JobStatus.PENDING)
            .values(status=JobStatus.RUNNING, started_at=datetime.now(UTC))
        ),
    )
    if result.rowcount != 1:
        session.rollback()
        raise JobTransitionError("Only a pending job can be claimed")
    job = session.execute(select(Job).where(Job.id == job_id)).scalar_one_or_none()
    if job is None:
        session.rollback()
        raise JobNotFoundError
    session.commit()
    return job


def complete_running_job(session: Session, job: Job) -> Job:
    """Complete a running job that carries no entity-coupled state."""
    if job.status != JobStatus.RUNNING:
        raise JobTransitionError("Only a running job can be completed")
    job.status = JobStatus.COMPLETED
    job.completed_at = datetime.now(UTC)
    job.failed_at = None
    job.error_code = None
    job.error_message = None
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise
    return job


def fail_running_job(session: Session, job: Job, code: str, message: str) -> Job:
    """Fail a running job that carries no entity-coupled state."""
    if job.status != JobStatus.RUNNING:
        raise JobTransitionError("Only a running job can be failed")
    job.status = JobStatus.FAILED
    job.completed_at = None
    job.failed_at = datetime.now(UTC)
    job.error_code = code
    job.error_message = message
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise
    return job


def _active_subject_job(
    session: Session, subject_type: str, subject_id: UUID
) -> Job | None:
    return session.execute(
        select(Job).where(
            Job.subject_type == subject_type,
            Job.subject_id == subject_id,
            Job.status.in_([JobStatus.PENDING, JobStatus.RUNNING]),
        )
    ).scalar_one_or_none()


def get_or_create_active_subject_job(
    session: Session,
    *,
    job_type: JobType,
    candidate_id: UUID,
    subject_type: str,
    subject_id: UUID,
) -> SubjectJobRequestResult:
    """Return the active Job for a subject or create the next pending one.

    The partial unique index on active (subject_type, subject_id) guarantees at
    most one pending/running Job per subject even under concurrent requests.
    """
    active = _active_subject_job(session, subject_type, subject_id)
    if active is not None:
        return SubjectJobRequestResult(job=active, created=False)

    job = Job(
        job_type=job_type,
        status=JobStatus.PENDING,
        candidate_id=candidate_id,
        subject_type=subject_type,
        subject_id=subject_id,
    )
    session.add(job)
    try:
        session.commit()
    except IntegrityError:
        # The partial unique index may have been won by a concurrent request.
        session.rollback()
        active = _active_subject_job(session, subject_type, subject_id)
        if active is not None:
            return SubjectJobRequestResult(job=active, created=False)
        raise
    except SQLAlchemyError:
        session.rollback()
        raise
    return SubjectJobRequestResult(job=job, created=True)
