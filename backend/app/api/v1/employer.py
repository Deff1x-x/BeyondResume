from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.dependencies import require_employer
from app.api.errors import api_error
from app.db.session import get_db
from app.models.employer_profile import EmployerProfile
from app.models.user import User
from app.schemas.employer import (
    EmployerCompanyCreateRequest,
    EmployerCompanyResponse,
    MatchSkillGroupResponse,
    SkillOptionResponse,
    VacancyCreateRequest,
    VacancyMatchResponse,
    VacancyMatchesResponse,
    VacancyRequirementCreateRequest,
    VacancyRequirementResponse,
    VacancyRequirementType,
    VacancyResponse,
)
from app.services.employer import (
    EmployerCompanyAlreadyExistsError,
    SkillNotAvailableError,
    VacancyRequirementConflictError,
    VacancyRequirementNotFoundError,
    add_vacancy_requirement,
    create_employer_company,
    create_vacancy,
    delete_vacancy_requirement,
    get_employer_company,
    get_vacancy,
    list_available_skills,
    list_vacancies,
    list_vacancy_matches,
    list_vacancy_requirements,
)

router = APIRouter(prefix="/employer", tags=["employer"])


def _require_company(session: Session, user_id: UUID) -> EmployerProfile:
    company = get_employer_company(session, user_id)
    if company is None:
        raise api_error(
            409,
            "EMPLOYER_COMPANY_REQUIRED",
            "Create a company before managing vacancies",
        )
    return company


@router.get("/company", response_model=EmployerCompanyResponse)
def get_company(
    current_user: Annotated[User, Depends(require_employer)],
    session: Annotated[Session, Depends(get_db)],
) -> EmployerCompanyResponse:
    company = get_employer_company(session, current_user.id)
    if company is None:
        raise api_error(404, "EMPLOYER_COMPANY_NOT_FOUND", "Company not found")
    return EmployerCompanyResponse.model_validate(company)


@router.post("/company", response_model=EmployerCompanyResponse, status_code=201)
def create_company(
    request: EmployerCompanyCreateRequest,
    current_user: Annotated[User, Depends(require_employer)],
    session: Annotated[Session, Depends(get_db)],
) -> EmployerCompanyResponse:
    try:
        company = create_employer_company(
            session,
            current_user.id,
            company_name=request.company_name,
            website=str(request.website) if request.website is not None else None,
            description=request.description,
        )
    except EmployerCompanyAlreadyExistsError:
        raise api_error(
            409,
            "EMPLOYER_COMPANY_ALREADY_EXISTS",
            "A company is already registered for this employer",
        ) from None
    except SQLAlchemyError:
        raise api_error(500, "DATABASE_ERROR", "Database operation failed") from None
    return EmployerCompanyResponse.model_validate(company)


@router.get("/vacancies", response_model=list[VacancyResponse])
def get_vacancies(
    current_user: Annotated[User, Depends(require_employer)],
    session: Annotated[Session, Depends(get_db)],
) -> list[VacancyResponse]:
    company = _require_company(session, current_user.id)
    vacancies = list_vacancies(session, company.id)
    return [VacancyResponse.model_validate(vacancy) for vacancy in vacancies]


@router.post("/vacancies", response_model=VacancyResponse, status_code=201)
def post_vacancy(
    request: VacancyCreateRequest,
    current_user: Annotated[User, Depends(require_employer)],
    session: Annotated[Session, Depends(get_db)],
) -> VacancyResponse:
    company = _require_company(session, current_user.id)
    try:
        vacancy = create_vacancy(
            session,
            company.id,
            title=request.title,
            description=request.description,
            status=request.status,
        )
    except SQLAlchemyError:
        raise api_error(500, "DATABASE_ERROR", "Database operation failed") from None
    return VacancyResponse.model_validate(vacancy)


@router.get("/vacancies/{vacancy_id}", response_model=VacancyResponse)
def get_vacancy_detail(
    vacancy_id: UUID,
    current_user: Annotated[User, Depends(require_employer)],
    session: Annotated[Session, Depends(get_db)],
) -> VacancyResponse:
    company = _require_company(session, current_user.id)
    vacancy = get_vacancy(session, company.id, vacancy_id)
    if vacancy is None:
        raise api_error(404, "VACANCY_NOT_FOUND", "Vacancy not found")
    return VacancyResponse.model_validate(vacancy)


def _require_owned_vacancy(
    session: Session, user_id: UUID, vacancy_id: UUID
) -> EmployerProfile:
    company = _require_company(session, user_id)
    vacancy = get_vacancy(session, company.id, vacancy_id)
    if vacancy is None:
        raise api_error(404, "VACANCY_NOT_FOUND", "Vacancy not found")
    return company


def _requirement_response(
    requirement_id: UUID,
    skill_id: UUID,
    skill_name: str,
    skill_category: str,
    requirement_type: str,
) -> VacancyRequirementResponse:
    return VacancyRequirementResponse(
        id=requirement_id,
        skill_id=skill_id,
        skill_name=skill_name,
        skill_category=skill_category,
        requirement_type=cast(VacancyRequirementType, requirement_type),
    )


@router.get("/skills", response_model=list[SkillOptionResponse])
def get_skills(
    current_user: Annotated[User, Depends(require_employer)],
    session: Annotated[Session, Depends(get_db)],
) -> list[SkillOptionResponse]:
    _ = current_user
    skills = list_available_skills(session)
    return [
        SkillOptionResponse(id=skill.id, name=skill.canonical_name, category=skill.category)
        for skill in skills
    ]


@router.get(
    "/vacancies/{vacancy_id}/requirements",
    response_model=list[VacancyRequirementResponse],
)
def get_vacancy_requirements(
    vacancy_id: UUID,
    current_user: Annotated[User, Depends(require_employer)],
    session: Annotated[Session, Depends(get_db)],
) -> list[VacancyRequirementResponse]:
    _require_owned_vacancy(session, current_user.id, vacancy_id)
    rows = list_vacancy_requirements(session, vacancy_id)
    return [
        _requirement_response(
            requirement.id,
            skill.id,
            skill.canonical_name,
            skill.category,
            requirement.requirement_type,
        )
        for requirement, skill in rows
    ]


@router.post(
    "/vacancies/{vacancy_id}/requirements",
    response_model=VacancyRequirementResponse,
    status_code=201,
)
def post_vacancy_requirement(
    vacancy_id: UUID,
    request: VacancyRequirementCreateRequest,
    current_user: Annotated[User, Depends(require_employer)],
    session: Annotated[Session, Depends(get_db)],
) -> VacancyRequirementResponse:
    _require_owned_vacancy(session, current_user.id, vacancy_id)
    try:
        requirement, skill = add_vacancy_requirement(
            session,
            vacancy_id,
            skill_id=request.skill_id,
            requirement_type=request.requirement_type,
        )
    except SkillNotAvailableError:
        raise api_error(404, "SKILL_NOT_FOUND", "Skill not found") from None
    except VacancyRequirementConflictError:
        raise api_error(
            409,
            "VACANCY_REQUIREMENT_CONFLICT",
            "This skill is already linked to the vacancy",
        ) from None
    except SQLAlchemyError:
        raise api_error(500, "DATABASE_ERROR", "Database operation failed") from None
    return _requirement_response(
        requirement.id,
        skill.id,
        skill.canonical_name,
        skill.category,
        requirement.requirement_type,
    )


@router.delete(
    "/vacancies/{vacancy_id}/requirements/{requirement_id}",
    status_code=204,
)
def remove_vacancy_requirement(
    vacancy_id: UUID,
    requirement_id: UUID,
    current_user: Annotated[User, Depends(require_employer)],
    session: Annotated[Session, Depends(get_db)],
) -> Response:
    _require_owned_vacancy(session, current_user.id, vacancy_id)
    try:
        delete_vacancy_requirement(session, vacancy_id, requirement_id)
    except VacancyRequirementNotFoundError:
        raise api_error(404, "VACANCY_REQUIREMENT_NOT_FOUND", "Requirement not found") from None
    except SQLAlchemyError:
        raise api_error(500, "DATABASE_ERROR", "Database operation failed") from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/vacancies/{vacancy_id}/matches",
    response_model=VacancyMatchesResponse,
)
def get_vacancy_matches(
    vacancy_id: UUID,
    current_user: Annotated[User, Depends(require_employer)],
    session: Annotated[Session, Depends(get_db)],
) -> VacancyMatchesResponse:
    _require_owned_vacancy(session, current_user.id, vacancy_id)
    matches = list_vacancy_matches(session, vacancy_id)
    return VacancyMatchesResponse(
        matches=[
            VacancyMatchResponse(
                candidate_id=item.candidate_id,
                candidate_name=item.candidate_name,
                score=item.result.score,
                required=MatchSkillGroupResponse(
                    matched=list(item.result.required.matched),
                    missing=list(item.result.required.missing),
                ),
                preferred=MatchSkillGroupResponse(
                    matched=list(item.result.preferred.matched),
                    missing=list(item.result.preferred.missing),
                ),
            )
            for item in matches
        ]
    )
