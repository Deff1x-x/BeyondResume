from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.dependencies import require_candidate
from app.api.errors import api_error
from app.db.session import get_db
from app.models.user import User
from app.schemas.resume import ResumeUploadResponse
from app.services.resume import (
    CandidateProfileRequiredError,
    EmptyResumeFileError,
    MissingResumeFilenameError,
    ResumeFileTooLargeError,
    ResumeFilenameTooLongError,
    ResumeStorageError,
    UnsupportedResumeTypeError,
    upload_resume,
)

router = APIRouter(prefix="/candidate", tags=["candidate"])


@router.post("/resume", response_model=ResumeUploadResponse, status_code=201)
async def create_resume(
    file: Annotated[UploadFile, File()],
    current_user: Annotated[User, Depends(require_candidate)],
    session: Annotated[Session, Depends(get_db)],
) -> ResumeUploadResponse:
    try:
        resume = await upload_resume(session, current_user.id, file)
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
    return ResumeUploadResponse.model_validate(resume)
