from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import require_candidate
from app.db.session import get_db
from app.models.user import User
from app.schemas.roadmap import RoadmapResponse
from app.services.candidate import get_candidate_profile
from app.services.roadmap import build_roadmap_from_passport
from app.services.skill_passport import (
    build_passport as _build_passport,
    empty_passport as _empty_passport,
)

router = APIRouter(prefix="/candidate/roadmap", tags=["roadmap"])


@router.get("", response_model=RoadmapResponse)
def get_roadmap(
    current_user: Annotated[User, Depends(require_candidate)],
    session: Annotated[Session, Depends(get_db)],
) -> RoadmapResponse:
    profile = get_candidate_profile(session, current_user.id)
    if profile is None:
        passport = _empty_passport()
    else:
        passport = _build_passport(session, profile.id)
    return build_roadmap_from_passport(passport)
