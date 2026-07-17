from datetime import UTC, datetime
from typing import cast
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.job import Job, JobStatus, JobType
from app.models.resume import Resume


class JobNotFoundError(Exception):
    """The requested job does not exist."""


class JobTransitionError(Exception):
    """The requested job lifecycle transition is not allowed."""


class ResumeTransitionError(Exception):
    """The requested resume lifecycle transition is not allowed."""


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


def complete_job(session: Session, job: Job) -> Job:
    if (
        job.status != JobStatus.RUNNING
        or job.job_type != JobType.RESUME_PARSE
        or job.resume_id is None
    ):
        raise JobTransitionError("Only a running resume parse job can be completed")
    resume = session.execute(select(Resume).where(Resume.id == job.resume_id)).scalar_one()
    if resume.parse_status != "uploaded":
        raise ResumeTransitionError("Only an uploaded resume can be marked parsed")
    now = datetime.now(UTC)
    job.status = JobStatus.COMPLETED
    job.completed_at = now
    job.failed_at = None
    job.error_code = None
    job.error_message = None
    resume.parse_status = "parsed"
    resume.parsed_at = now
    resume.failed_at = None
    resume.parse_error_code = None
    resume.parse_error_message = None
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise
    return job


def fail_job(session: Session, job: Job, code: str, message: str) -> Job:
    if (
        job.status != JobStatus.RUNNING
        or job.job_type != JobType.RESUME_PARSE
        or job.resume_id is None
    ):
        raise JobTransitionError("Only a running resume parse job can be failed")
    resume = session.execute(select(Resume).where(Resume.id == job.resume_id)).scalar_one()
    if resume.parse_status != "uploaded":
        raise ResumeTransitionError("Only an uploaded resume can be marked failed")
    now = datetime.now(UTC)
    job.status = JobStatus.FAILED
    job.completed_at = None
    job.failed_at = now
    job.error_code = code
    job.error_message = message
    resume.parse_status = "failed"
    resume.failed_at = now
    resume.parse_error_code = code
    resume.parse_error_message = message
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise
    return job


def retry_failed_resume(session: Session, resume: Resume) -> Job:
    if resume.parse_status != "failed":
        raise ResumeTransitionError("Only a failed resume can be retried")
    active = session.execute(
        select(Job).where(
            Job.resume_id == resume.id,
            Job.job_type == JobType.RESUME_PARSE,
            Job.status.in_([JobStatus.PENDING, JobStatus.RUNNING]),
        )
    ).scalar_one_or_none()
    if active is not None:
        return active
    job = Job(resume_id=resume.id, job_type=JobType.RESUME_PARSE, status=JobStatus.PENDING)
    # `uploaded` is the only non-terminal state in the specified Resume lifecycle.
    # A retry therefore reopens the failed resume before its new Job is committed.
    resume.parse_status = "uploaded"
    session.add(job)
    try:
        session.commit()
    except IntegrityError:
        # The partial unique index may have been won by a concurrent retry.
        session.rollback()
        active = session.execute(
            select(Job).where(
                Job.resume_id == resume.id,
                Job.job_type == JobType.RESUME_PARSE,
                Job.status.in_([JobStatus.PENDING, JobStatus.RUNNING]),
            )
        ).scalar_one_or_none()
        if active is not None:
            return active
        raise
    except SQLAlchemyError:
        session.rollback()
        raise
    return job


def request_resume_parse(session: Session, resume: Resume) -> Job:
    """Return an active parse Job or create the next allowed parse attempt."""
    active = session.execute(
        select(Job).where(
            Job.resume_id == resume.id,
            Job.job_type == JobType.RESUME_PARSE,
            Job.status.in_([JobStatus.PENDING, JobStatus.RUNNING]),
        )
    ).scalar_one_or_none()
    if active is not None:
        return active
    if resume.parse_status == "failed":
        return retry_failed_resume(session, resume)
    if resume.parse_status != "uploaded":
        raise ResumeTransitionError("Resume parsing is not available for this status")

    job = Job(resume_id=resume.id, job_type=JobType.RESUME_PARSE, status=JobStatus.PENDING)
    session.add(job)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        active = session.execute(
            select(Job).where(
                Job.resume_id == resume.id,
                Job.job_type == JobType.RESUME_PARSE,
                Job.status.in_([JobStatus.PENDING, JobStatus.RUNNING]),
            )
        ).scalar_one_or_none()
        if active is not None:
            return active
        raise
    except SQLAlchemyError:
        session.rollback()
        raise
    return job


def is_retry_available(session: Session, job: Job, resume: Resume) -> bool:
    """Return whether this failed parse attempt may create a new pending job."""
    if (
        job.job_type != JobType.RESUME_PARSE
        or job.status != JobStatus.FAILED
        or resume.parse_status != "failed"
    ):
        return False
    active = session.execute(
        select(Job.id).where(
            Job.resume_id == resume.id,
            Job.job_type == JobType.RESUME_PARSE,
            Job.status.in_([JobStatus.PENDING, JobStatus.RUNNING]),
        )
    ).scalar_one_or_none()
    return active is None
