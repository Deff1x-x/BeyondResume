from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import require_candidate
from app.api.errors import api_error
from app.db.session import get_db
from app.models.user import User
from app.schemas.evidence import EvidenceHubListResponse
from app.services.candidate import get_candidate_profile
from app.services.evidence_hub import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    EvidenceHubQuery,
    list_candidate_evidence,
)

router = APIRouter(prefix="/candidate", tags=["evidence"])


@router.get("/evidence", response_model=EvidenceHubListResponse)
def get_candidate_evidence(
    current_user: Annotated[User, Depends(require_candidate)],
    session: Annotated[Session, Depends(get_db)],
    source_type: Annotated[str | None, Query(max_length=64)] = None,
    skill: Annotated[str | None, Query(max_length=120)] = None,
    search: Annotated[str | None, Query(max_length=200)] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> EvidenceHubListResponse:
    profile = get_candidate_profile(session, current_user.id)
    if profile is None:
        raise api_error(404, "PROFILE_NOT_FOUND", "Candidate profile not found")

    return list_candidate_evidence(
        session,
        candidate_id=profile.id,
        query=EvidenceHubQuery(
            source_type=source_type,
            skill=skill,
            search=search,
            limit=limit,
            offset=offset,
        ),
    )
