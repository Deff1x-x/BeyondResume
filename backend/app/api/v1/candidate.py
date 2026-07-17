from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.dependencies import require_candidate
from app.api.errors import api_error
from app.db.session import get_db
from app.models.user import User
from app.schemas.candidate import CandidateProfilePatchRequest, CandidateProfileResponse
from app.services.candidate import (
    MissingCandidateProfileFullNameError,
    get_candidate_profile,
    patch_candidate_profile,
)

router = APIRouter(prefix="/candidate", tags=["candidate"])


@router.get("/profile", response_model=CandidateProfileResponse)
def get_profile(
    current_user: Annotated[User, Depends(require_candidate)],
    session: Annotated[Session, Depends(get_db)],
) -> CandidateProfileResponse:
    profile = get_candidate_profile(session, current_user.id)
    if profile is None:
        raise api_error(404, "CANDIDATE_PROFILE_NOT_FOUND", "Candidate profile not found")
    return CandidateProfileResponse.model_validate(profile)


@router.patch("/profile", response_model=CandidateProfileResponse)
def patch_profile(
    patch: CandidateProfilePatchRequest,
    current_user: Annotated[User, Depends(require_candidate)],
    session: Annotated[Session, Depends(get_db)],
) -> CandidateProfileResponse:
    try:
        profile = patch_candidate_profile(
            session, current_user.id, patch.model_dump(exclude_unset=True)
        )
    except MissingCandidateProfileFullNameError:
        raise api_error(
            422,
            "VALIDATION_ERROR",
            "Validation error",
            details=[{"field": "full_name", "issue": "missing"}],
        ) from None
    except SQLAlchemyError:
        raise api_error(500, "DATABASE_ERROR", "Database operation failed") from None
    return CandidateProfileResponse.model_validate(profile)
