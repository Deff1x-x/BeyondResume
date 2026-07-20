from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.dependencies import require_candidate
from app.api.errors import api_error
from app.db.session import get_db
from app.models.user import User
from app.schemas.candidate import (
    CandidateProfilePatchRequest,
    CandidateProfileResponse,
    CandidateVacancyDetailResponse,
    CandidateVacancyListItemResponse,
)
from app.services.candidate import (
    CandidateProfileNotFoundError,
    get_candidate_profile,
    patch_candidate_profile,
)
from app.services.candidate_vacancies import (
    CandidateVacancyNotFoundError,
    get_candidate_vacancy,
    list_candidate_vacancies,
    vacancy_roadmap,
)
from app.schemas.employer import MatchDetailsMatchResponse, MatchDetailsRoadmapItemResponse, MatchSkillGroupResponse

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
    except CandidateProfileNotFoundError:
        raise api_error(404, "CANDIDATE_PROFILE_NOT_FOUND", "Candidate profile not found") from None
    except SQLAlchemyError:
        raise api_error(500, "DATABASE_ERROR", "Database operation failed") from None
    return CandidateProfileResponse.model_validate(profile)


def _match_response(match) -> MatchDetailsMatchResponse:
    return MatchDetailsMatchResponse(
        score=match.score,
        required=MatchSkillGroupResponse(
            matched=list(match.required.matched), missing=list(match.required.missing)
        ),
        preferred=MatchSkillGroupResponse(
            matched=list(match.preferred.matched), missing=list(match.preferred.missing)
        ),
    )


def _vacancy_list_item(item) -> CandidateVacancyListItemResponse:
    return CandidateVacancyListItemResponse(
        id=item.vacancy.id,
        title=item.vacancy.title,
        company_name=item.company_name,
        description=item.vacancy.description,
        created_at=item.vacancy.created_at,
        match=_match_response(item.match),
        required_skills=list(item.required_skills),
        preferred_skills=list(item.preferred_skills),
    )


@router.get("/vacancies", response_model=list[CandidateVacancyListItemResponse])
def get_vacancies(
    current_user: Annotated[User, Depends(require_candidate)],
    session: Annotated[Session, Depends(get_db)],
) -> list[CandidateVacancyListItemResponse]:
    profile = get_candidate_profile(session, current_user.id)
    if profile is None:
        return []
    return [_vacancy_list_item(item) for item in list_candidate_vacancies(session, profile.id)]


@router.get("/vacancies/{vacancy_id}", response_model=CandidateVacancyDetailResponse)
def get_vacancy(
    vacancy_id: UUID,
    current_user: Annotated[User, Depends(require_candidate)],
    session: Annotated[Session, Depends(get_db)],
) -> CandidateVacancyDetailResponse:
    profile = get_candidate_profile(session, current_user.id)
    if profile is None:
        raise api_error(404, "CANDIDATE_PROFILE_NOT_FOUND", "Candidate profile not found")
    try:
        item = get_candidate_vacancy(session, profile.id, vacancy_id)
    except CandidateVacancyNotFoundError:
        raise api_error(404, "VACANCY_NOT_FOUND", "Vacancy not found") from None
    roadmap = vacancy_roadmap(item.match)
    return CandidateVacancyDetailResponse(
        **_vacancy_list_item(item).model_dump(),
        roadmap=[
            MatchDetailsRoadmapItemResponse.model_validate(roadmap_item.model_dump())
            for roadmap_item in roadmap.items
        ],
    )
