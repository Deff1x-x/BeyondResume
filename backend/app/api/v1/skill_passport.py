from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import require_candidate
from app.db.session import get_db
from app.models.user import User
from app.schemas.skill_passport import SkillPassportResponse
from app.services.candidate import get_candidate_profile
from app.services.skill_passport import build_passport, empty_passport

router = APIRouter(prefix="/candidate/skill-passport", tags=["skill-passport"])


@router.get("", response_model=SkillPassportResponse)
def get_skill_passport(
    current_user: Annotated[User, Depends(require_candidate)],
    session: Annotated[Session, Depends(get_db)],
) -> SkillPassportResponse:
    profile = get_candidate_profile(session, current_user.id)
    if profile is None:
        return empty_passport()
    return build_passport(session, profile.id)
