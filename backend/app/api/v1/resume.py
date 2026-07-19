from typing import Annotated, Literal, cast
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.dependencies import require_candidate
from app.api.errors import api_error
from app.db.session import get_db
from app.models.job import JobStatus
from app.models.user import User
from app.schemas.resume import JobPollingResponse, ResumeResponse, ResumeUploadAcceptedResponse
from app.services.resume import (
    CandidateProfileRequiredError,
    EmptyResumeFileError,
    MissingResumeFilenameError,
    ResumeFileTooLargeError,
    ResumeFilenameTooLongError,
    ResumeStorageError,
    UnsupportedResumeTypeError,
    upload_resume,
    get_current_resume,
    get_candidate_resume,
    get_download_path,
)
from app.services.resume_jobs import (
    ResumeTransitionError,
    request_resume_parse,
    retry_failed_resume,
)
from app.services.resume_parsing import run_resume_parse_job_task

router = APIRouter(prefix="/candidate", tags=["candidate"])


@router.post("/resumes", response_model=ResumeUploadAcceptedResponse, status_code=202)
async def create_resume(
    file: Annotated[UploadFile, File()],
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(require_candidate)],
    session: Annotated[Session, Depends(get_db)],
) -> ResumeUploadAcceptedResponse:
    try:
        upload_result = await upload_resume(session, current_user.id, file)
    except CandidateProfileRequiredError:
        raise api_error(
            409,
            "CANDIDATE_PROFILE_REQUIRED",
            "Create a candidate profile before uploading a resume",
        ) from None
    except UnsupportedResumeTypeError:
        raise api_error(
            415,
            "UNSUPPORTED_RESUME_TYPE",
            "Only PDF and DOCX resume files are supported",
            details=[{"field": "file", "issue": "unsupported_type"}],
        ) from None
    except ResumeFileTooLargeError:
        raise api_error(
            413,
            "RESUME_FILE_TOO_LARGE",
            "Resume file must not exceed 8 MiB",
            details=[{"field": "file", "issue": "file_too_large", "max_bytes": 8_388_608}],
        ) from None
    except EmptyResumeFileError:
        raise api_error(
            422,
            "VALIDATION_ERROR",
            "Validation error",
            details=[{"field": "file", "issue": "empty_file"}],
        ) from None
    except MissingResumeFilenameError:
        raise api_error(
            422,
            "VALIDATION_ERROR",
            "Validation error",
            details=[{"field": "file", "issue": "missing_filename"}],
        ) from None
    except ResumeFilenameTooLongError:
        raise api_error(
            422,
            "VALIDATION_ERROR",
            "Validation error",
            details=[{"field": "file", "issue": "filename_too_long", "max_length": 255}],
        ) from None
    except ResumeStorageError:
        raise api_error(500, "RESUME_STORAGE_ERROR", "Failed to store resume file") from None
    except SQLAlchemyError:
        raise api_error(500, "DATABASE_ERROR", "Database operation failed") from None
    background_tasks.add_task(run_resume_parse_job_task, upload_result.job.id)
    return ResumeUploadAcceptedResponse(
        resume_id=upload_result.resume.id,
        job_id=upload_result.job.id,
    )


@router.get("/resumes", response_model=ResumeResponse)
def get_resume(
    current_user: Annotated[User, Depends(require_candidate)],
    session: Annotated[Session, Depends(get_db)],
) -> ResumeResponse:
    resume = get_current_resume(session, current_user.id)
    if resume is None:
        raise api_error(404, "RESUME_NOT_FOUND", "Current resume not found")
    return ResumeResponse.model_validate(resume)


@router.get("/resumes/{resume_id}", response_model=ResumeResponse)
def get_resume_by_id(
    resume_id: UUID,
    current_user: Annotated[User, Depends(require_candidate)],
    session: Annotated[Session, Depends(get_db)],
) -> ResumeResponse:
    resume = get_candidate_resume(session, current_user.id, resume_id)
    if resume is None:
        raise api_error(404, "RESUME_NOT_FOUND", "Resume not found")
    return ResumeResponse.model_validate(resume)


@router.get("/resume/download")
def download_resume(
    current_user: Annotated[User, Depends(require_candidate)],
    session: Annotated[Session, Depends(get_db)],
) -> FileResponse:
    resume = get_current_resume(session, current_user.id)
    if resume is None:
        raise api_error(404, "RESUME_NOT_FOUND", "Current resume not found")
    try:
        path = get_download_path(resume)
    except ResumeStorageError:
        raise api_error(404, "RESUME_FILE_NOT_FOUND", "Resume file not found") from None
    return FileResponse(path, media_type=resume.mime_type, filename=resume.original_filename)


@router.post("/resumes/{resume_id}/parse", response_model=JobPollingResponse)
def request_resume_parsing(
    resume_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(require_candidate)],
    session: Annotated[Session, Depends(get_db)],
) -> JobPollingResponse:
    resume = get_candidate_resume(session, current_user.id, resume_id)
    if resume is None:
        raise api_error(404, "RESUME_NOT_FOUND", "Resume not found")
    try:
        job = request_resume_parse(session, resume)
    except ResumeTransitionError:
        raise api_error(
            409, "RESUME_PARSE_NOT_ALLOWED", "Resume parsing is not available"
        ) from None
    except SQLAlchemyError:
        session.rollback()
        raise api_error(500, "DATABASE_ERROR", "Database operation failed") from None

    if job.status == JobStatus.PENDING:
        background_tasks.add_task(run_resume_parse_job_task, job.id)
    return JobPollingResponse(
        id=job.id,
        status=job.status,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        failed_at=job.failed_at,
        error_code=job.error_code,
        error_message=job.error_message,
        resume_status=cast(Literal["uploaded", "parsed", "failed"], resume.parse_status),
        retry_available=False,
    )


@router.post("/resume/retry", response_model=JobPollingResponse, status_code=201)
def retry_resume_processing(
    current_user: Annotated[User, Depends(require_candidate)],
    session: Annotated[Session, Depends(get_db)],
) -> JobPollingResponse:
    resume = get_current_resume(session, current_user.id)
    if resume is None:
        raise api_error(404, "RESUME_NOT_FOUND", "Current resume not found")
    try:
        job = retry_failed_resume(session, resume)
    except ResumeTransitionError:
        raise api_error(409, "RESUME_RETRY_NOT_ALLOWED", "Resume retry is not available") from None
    except SQLAlchemyError:
        session.rollback()
        raise api_error(500, "DATABASE_ERROR", "Database operation failed") from None

    return JobPollingResponse(
        id=job.id,
        status=job.status,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        failed_at=job.failed_at,
        error_code=job.error_code,
        error_message=job.error_message,
        resume_status=cast(Literal["uploaded", "parsed", "failed"], resume.parse_status),
        retry_available=False,
    )
