from typing import Annotated
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


@router.get("/{job_id}", response_model=JobPollingResponse)
def get_job_status(
    job_id: UUID,
    current_user: Annotated[User, Depends(require_candidate)],
    session: Annotated[Session, Depends(get_db)],
) -> JobPollingResponse:
    row = session.execute(
        select(Job, Resume)
        .join(Resume, Job.resume_id == Resume.id)
        .join(CandidateProfile, Resume.candidate_id == CandidateProfile.id)
        .where(Job.id == job_id, CandidateProfile.user_id == current_user.id)
    ).one_or_none()
    if row is None:
        raise api_error(404, "JOB_NOT_FOUND", "Job not found")

    job, resume = row
    return JobPollingResponse(
        id=job.id,
        status=job.status,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        failed_at=job.failed_at,
        error_code=job.error_code,
        error_message=job.error_message,
        resume_status=resume.parse_status,
        retry_available=is_retry_available(session, job, resume),
    )
