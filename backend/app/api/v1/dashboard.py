from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import require_candidate
from app.db.session import get_db
from app.models.user import User
from app.schemas.dashboard import CandidateDashboardResponse
from app.services.candidate import get_candidate_profile
from app.services.dashboard import build_candidate_dashboard

router = APIRouter(prefix="/candidate/dashboard", tags=["dashboard"])


@router.get("", response_model=CandidateDashboardResponse)
def get_candidate_dashboard(
    current_user: Annotated[User, Depends(require_candidate)],
    session: Annotated[Session, Depends(get_db)],
) -> CandidateDashboardResponse:
    profile = get_candidate_profile(session, current_user.id)
    return build_candidate_dashboard(session, None if profile is None else profile.id)
