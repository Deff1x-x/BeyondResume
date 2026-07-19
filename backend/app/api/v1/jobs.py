from typing import Annotated, Literal, cast
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import require_candidate
from app.api.errors import api_error
from app.db.session import get_db
from app.models.candidate_profile import CandidateProfile
from app.models.job import Job
from app.models.resume import Resume
from app.models.user import User
from app.schemas.resume import JobPollingResponse
from app.services.resume_jobs import is_retry_available

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _job_not_found() -> Exception:
    return api_error(404, "JOB_NOT_FOUND", "Job not found")


def _get_owned_resume(session: Session, user_id: UUID, resume_id: UUID) -> Resume | None:
    return session.execute(
        select(Resume)
        .join(CandidateProfile, Resume.candidate_id == CandidateProfile.id)
        .where(Resume.id == resume_id, CandidateProfile.user_id == user_id)
    ).scalar_one_or_none()


def _owns_candidate_profile(session: Session, user_id: UUID, candidate_id: UUID) -> bool:
    profile_id = session.execute(
        select(CandidateProfile.id).where(
            CandidateProfile.id == candidate_id, CandidateProfile.user_id == user_id
        )
    ).scalar_one_or_none()
    return profile_id is not None


@router.get("/{job_id}", response_model=JobPollingResponse)
def get_job_status(
    job_id: UUID,
    current_user: Annotated[User, Depends(require_candidate)],
    session: Annotated[Session, Depends(get_db)],
) -> JobPollingResponse:
    job = session.execute(select(Job).where(Job.id == job_id)).scalar_one_or_none()
    if job is None:
        raise _job_not_found()

    resume: Resume | None = None
    if job.resume_id is not None:
        resume = _get_owned_resume(session, current_user.id, job.resume_id)
        if resume is None:
            raise _job_not_found()
    elif job.candidate_id is not None:
        if not _owns_candidate_profile(session, current_user.id, job.candidate_id):
            raise _job_not_found()
    else:
        # A job without owner context is not exposed to candidates.
        raise _job_not_found()

    return JobPollingResponse(
        id=job.id,
        job_type=job.job_type,
        status=job.status,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        failed_at=job.failed_at,
        error_code=job.error_code,
        error_message=job.error_message,
        resume_status=(
            cast(Literal["uploaded", "parsed", "failed"], resume.parse_status)
            if resume is not None
            else None
        ),
        retry_available=(
            is_retry_available(session, job, resume) if resume is not None else False
        ),
    )
