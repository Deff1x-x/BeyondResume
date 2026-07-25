from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import require_candidate
from app.db.session import get_db
from app.models.user import User
from app.schemas.roadmap import RoadmapItemResponse, RoadmapPriority, RoadmapResponse
from app.services.candidate import get_candidate_profile
from app.services.career_companion.plan_service import get_active_plan
from app.services.roadmap import build_roadmap_from_passport
from app.services.skill_passport import (
    build_passport as _build_passport,
    empty_passport as _empty_passport,
)

router = APIRouter(prefix="/candidate/roadmap", tags=["roadmap"])


def _priority_from_score(score: float) -> RoadmapPriority:
    if score >= 55:
        return "high"
    if score >= 35:
        return "medium"
    return "low"


def _fix_now_from_companion(session: Session, candidate_id) -> RoadmapResponse | None:
    """Prefer active Career Companion Fix Now titles when a real plan exists."""
    try:
        plan = get_active_plan(session, candidate_id)
    except Exception:
        return None
    if plan is None:
        return None
    actions = getattr(plan, "actions", None)
    if not isinstance(actions, (list, tuple)):
        return None
    fix_now = [action for action in actions if getattr(action, "horizon", None) == "fix_now"]
    if not fix_now:
        return None
    return RoadmapResponse(
        items=[
            RoadmapItemResponse(
                id=str(action.id),
                title=action.title,
                reason=action.why_it_matters,
                priority=_priority_from_score(float(action.priority_score)),
                missing_skills=[
                    skill.skill_name
                    for skill in (getattr(action, "skills", None) or [])
                    if skill.role == "gap"
                ],
                related_skills=[
                    skill.skill_name
                    for skill in (getattr(action, "skills", None) or [])
                    if skill.role != "gap"
                ],
            )
            for action in fix_now[:3]
        ]
    )


@router.get("", response_model=RoadmapResponse)
def get_roadmap(
    current_user: Annotated[User, Depends(require_candidate)],
    session: Annotated[Session, Depends(get_db)],
) -> RoadmapResponse:
    """Thin adapter: prefer Companion Fix Now when available, else passport rules."""
    profile = get_candidate_profile(session, current_user.id)
    if profile is None:
        passport = _empty_passport()
        return build_roadmap_from_passport(passport)

    companion = _fix_now_from_companion(session, profile.id)
    if companion is not None:
        return companion

    passport = _build_passport(session, profile.id)
    return build_roadmap_from_passport(passport)
