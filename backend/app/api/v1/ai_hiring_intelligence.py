from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import require_candidate
from app.api.errors import api_error
from app.db.session import get_db
from app.models.user import User
from app.schemas.ai_hiring_intelligence import AiHiringIntelligenceResponse
from app.services.ai_hiring_intelligence import (
    HiringIntelligenceUnavailableError,
    build_hiring_context,
    get_hiring_intelligence,
)
from app.services.candidate import get_candidate_profile
from app.services.skill_passport import build_passport, empty_passport

router = APIRouter(prefix="/candidate/ai-hiring-intelligence", tags=["ai-hiring-intelligence"])


@router.get("", response_model=AiHiringIntelligenceResponse)
def get_ai_hiring_intelligence(
    current_user: Annotated[User, Depends(require_candidate)],
    session: Annotated[Session, Depends(get_db)],
) -> AiHiringIntelligenceResponse:
    profile = get_candidate_profile(session, current_user.id)
    passport = build_passport(session, profile.id) if profile is not None else empty_passport()
    context = build_hiring_context(candidate_name=profile.display_name if profile else None, passport=passport)
    try:
        return get_hiring_intelligence(context)
    except HiringIntelligenceUnavailableError:
        raise api_error(503, "AI_HIRING_INTELLIGENCE_UNAVAILABLE", "AI analysis is temporarily unavailable.") from None
