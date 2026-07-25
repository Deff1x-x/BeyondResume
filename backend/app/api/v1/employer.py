from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.dependencies import require_employer
from app.api.errors import api_error
from app.db.session import get_db
from app.models.employer_profile import EmployerProfile
from app.models.user import User
from app.models.vacancy import Vacancy
from app.schemas.employer import (
    AiMatchExplanationResponse,
    EmployerCompanyCreateRequest,
    EmployerCompanyResponse,
    EmployerCompanyUpdateRequest,
    EmployerShortlistEntryResponse,
    EmployerShortlistListResponse,
    EmployerShortlistNoteUpdateRequest,
    EmployerShortlistStageUpdateRequest,
    MatchDetailsResponse,
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
from app.services.ai_match_explanation import (
    MatchExplanationUnavailableError,
    build_explanation_input,
    explain_match,
)
from app.services.ai_hiring_intelligence import (
    HiringIntelligenceUnavailableError,
    build_hiring_context,
    get_hiring_intelligence,
)
from app.schemas.ai_hiring_intelligence import AiHiringIntelligenceResponse
from app.schemas.interview_questions import InterviewQuestionsResponse
from app.schemas.interview_scorecard import (
    InterviewScorecardResponse,
    InterviewScorecardUpsertRequest,
)
from app.services.employer import (
    EmployerCompanyAlreadyExistsError,
    EmployerCompanyNotFoundError,
    SkillNotAvailableError,
    VacancyNotFoundError,
    VacancyRequirementConflictError,
    VacancyRequirementNotFoundError,
    add_vacancy_requirement,
    create_employer_company,
    create_vacancy,
    delete_vacancy,
    delete_vacancy_requirement,
    get_employer_company,
    get_vacancy,
    list_available_skills,
    list_vacancies,
    list_vacancy_matches,
    list_vacancy_requirements,
    update_employer_company,
)
from app.services.match_details import (
    MatchDetailsCandidateNotFoundError,
    build_match_details,
)
from app.services.employer_shortlist import (
    ShortlistCandidateNotFoundError,
    ShortlistEntryNotFoundError,
    ShortlistPersistenceError,
    list_shortlisted_candidates,
    remove_candidate_from_shortlist,
    save_candidate_to_shortlist,
    update_candidate_note,
    update_candidate_stage,
)
from app.services.interview_questions import (
    InterviewQuestionsUnavailableError,
    build_interview_questions_context,
    get_interview_questions,
)
from app.services.interview_scorecard import (
    ScorecardCandidateNotFoundError,
    ScorecardNotFoundError,
    get_interview_scorecard,
    upsert_interview_scorecard,
)
from app.services.skill_passport import build_passport

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


@router.patch("/company", response_model=EmployerCompanyResponse)
def update_company(
    request: EmployerCompanyUpdateRequest,
    current_user: Annotated[User, Depends(require_employer)],
    session: Annotated[Session, Depends(get_db)],
) -> EmployerCompanyResponse:
    fields_set = request.model_fields_set
    if not fields_set:
        raise api_error(
            422,
            "VALIDATION_ERROR",
            "At least one company field must be provided",
        )
    try:
        company = update_employer_company(
            session,
            current_user.id,
            company_name=request.company_name if "company_name" in fields_set else None,
            website=str(request.website) if request.website is not None else None,
            description=request.description,
            website_set="website" in fields_set,
            description_set="description" in fields_set,
        )
    except EmployerCompanyNotFoundError:
        raise api_error(404, "EMPLOYER_COMPANY_NOT_FOUND", "Company not found") from None
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


@router.delete("/vacancies/{vacancy_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_vacancy(
    vacancy_id: UUID,
    current_user: Annotated[User, Depends(require_employer)],
    session: Annotated[Session, Depends(get_db)],
) -> Response:
    company = _require_company(session, current_user.id)
    try:
        delete_vacancy(session, company.id, vacancy_id)
    except VacancyNotFoundError:
        raise api_error(404, "VACANCY_NOT_FOUND", "Vacancy not found") from None
    except SQLAlchemyError:
        raise api_error(500, "DATABASE_ERROR", "Database operation failed") from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _require_owned_vacancy(session: Session, user_id: UUID, vacancy_id: UUID) -> EmployerProfile:
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


def _owned_vacancy(session: Session, user_id: UUID, vacancy_id: UUID) -> Vacancy:
    company = _require_owned_vacancy(session, user_id, vacancy_id)
    vacancy = get_vacancy(session, company.id, vacancy_id)
    if vacancy is None:
        raise api_error(404, "VACANCY_NOT_FOUND", "Vacancy not found")
    return vacancy


@router.put(
    "/vacancies/{vacancy_id}/shortlist/{candidate_id}",
    response_model=EmployerShortlistEntryResponse,
)
def put_shortlisted_candidate(
    vacancy_id: UUID,
    candidate_id: UUID,
    current_user: Annotated[User, Depends(require_employer)],
    session: Annotated[Session, Depends(get_db)],
) -> EmployerShortlistEntryResponse:
    vacancy = _owned_vacancy(session, current_user.id, vacancy_id)
    try:
        entry = save_candidate_to_shortlist(
            session,
            vacancy=vacancy,
            candidate_id=candidate_id,
        )
    except ShortlistCandidateNotFoundError:
        raise api_error(
            404, "CANDIDATE_NOT_FOUND", "Candidate not found or unavailable"
        ) from None
    except (ShortlistPersistenceError, SQLAlchemyError):
        raise api_error(500, "DATABASE_ERROR", "Database operation failed") from None
    return EmployerShortlistEntryResponse.model_validate(entry)


@router.patch(
    "/vacancies/{vacancy_id}/shortlist/{candidate_id}",
    response_model=EmployerShortlistEntryResponse,
)
def patch_shortlisted_candidate_stage(
    vacancy_id: UUID,
    candidate_id: UUID,
    body: EmployerShortlistStageUpdateRequest,
    current_user: Annotated[User, Depends(require_employer)],
    session: Annotated[Session, Depends(get_db)],
) -> EmployerShortlistEntryResponse:
    vacancy = _owned_vacancy(session, current_user.id, vacancy_id)
    try:
        entry = update_candidate_stage(
            session,
            vacancy=vacancy,
            candidate_id=candidate_id,
            stage=body.stage,
        )
    except ShortlistEntryNotFoundError:
        raise api_error(404, "SHORTLIST_ENTRY_NOT_FOUND", "Shortlist entry not found") from None
    except ShortlistCandidateNotFoundError:
        raise api_error(
            404, "CANDIDATE_NOT_FOUND", "Candidate not found or unavailable"
        ) from None
    except SQLAlchemyError:
        raise api_error(500, "DATABASE_ERROR", "Database operation failed") from None
    return EmployerShortlistEntryResponse.model_validate(entry)


@router.patch(
    "/vacancies/{vacancy_id}/shortlist/{candidate_id}/note",
    response_model=EmployerShortlistEntryResponse,
)
def patch_shortlisted_candidate_note(
    vacancy_id: UUID,
    candidate_id: UUID,
    body: EmployerShortlistNoteUpdateRequest,
    current_user: Annotated[User, Depends(require_employer)],
    session: Annotated[Session, Depends(get_db)],
) -> EmployerShortlistEntryResponse:
    vacancy = _owned_vacancy(session, current_user.id, vacancy_id)
    try:
        entry = update_candidate_note(
            session,
            vacancy=vacancy,
            candidate_id=candidate_id,
            note=body.note,
        )
    except ShortlistEntryNotFoundError:
        raise api_error(404, "SHORTLIST_ENTRY_NOT_FOUND", "Shortlist entry not found") from None
    except ShortlistCandidateNotFoundError:
        raise api_error(
            404, "CANDIDATE_NOT_FOUND", "Candidate not found or unavailable"
        ) from None
    except SQLAlchemyError:
        raise api_error(500, "DATABASE_ERROR", "Database operation failed") from None
    return EmployerShortlistEntryResponse.model_validate(entry)


@router.delete(
    "/vacancies/{vacancy_id}/shortlist/{candidate_id}",
    status_code=204,
)
def delete_shortlisted_candidate(
    vacancy_id: UUID,
    candidate_id: UUID,
    current_user: Annotated[User, Depends(require_employer)],
    session: Annotated[Session, Depends(get_db)],
) -> Response:
    vacancy = _owned_vacancy(session, current_user.id, vacancy_id)
    try:
        remove_candidate_from_shortlist(
            session,
            vacancy=vacancy,
            candidate_id=candidate_id,
        )
    except SQLAlchemyError:
        raise api_error(500, "DATABASE_ERROR", "Database operation failed") from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/vacancies/{vacancy_id}/shortlist",
    response_model=EmployerShortlistListResponse,
)
def get_shortlisted_candidates(
    vacancy_id: UUID,
    current_user: Annotated[User, Depends(require_employer)],
    session: Annotated[Session, Depends(get_db)],
) -> EmployerShortlistListResponse:
    vacancy = _owned_vacancy(session, current_user.id, vacancy_id)
    try:
        entries = list_shortlisted_candidates(session, vacancy=vacancy)
    except SQLAlchemyError:
        raise api_error(500, "DATABASE_ERROR", "Database operation failed") from None
    return EmployerShortlistListResponse(
        entries=[EmployerShortlistEntryResponse.model_validate(entry) for entry in entries]
    )


@router.get(
    "/vacancies/{vacancy_id}/scorecards/{candidate_id}",
    response_model=InterviewScorecardResponse,
)
def get_vacancy_interview_scorecard(
    vacancy_id: UUID,
    candidate_id: UUID,
    current_user: Annotated[User, Depends(require_employer)],
    session: Annotated[Session, Depends(get_db)],
) -> InterviewScorecardResponse:
    vacancy = _owned_vacancy(session, current_user.id, vacancy_id)
    try:
        entry = get_interview_scorecard(
            session,
            vacancy=vacancy,
            candidate_id=candidate_id,
        )
    except ScorecardCandidateNotFoundError:
        raise api_error(
            404, "CANDIDATE_NOT_FOUND", "Candidate not found or unavailable"
        ) from None
    except ScorecardNotFoundError:
        raise api_error(404, "SCORECARD_NOT_FOUND", "Interview scorecard not found") from None
    except SQLAlchemyError:
        raise api_error(500, "DATABASE_ERROR", "Database operation failed") from None
    return InterviewScorecardResponse.model_validate(entry)


@router.put(
    "/vacancies/{vacancy_id}/scorecards/{candidate_id}",
    response_model=InterviewScorecardResponse,
)
def put_vacancy_interview_scorecard(
    vacancy_id: UUID,
    candidate_id: UUID,
    body: InterviewScorecardUpsertRequest,
    current_user: Annotated[User, Depends(require_employer)],
    session: Annotated[Session, Depends(get_db)],
) -> InterviewScorecardResponse:
    vacancy = _owned_vacancy(session, current_user.id, vacancy_id)
    try:
        entry = upsert_interview_scorecard(
            session,
            vacancy=vacancy,
            candidate_id=candidate_id,
            technical_competency=body.technical_competency,
            experience_relevance=body.experience_relevance,
            communication=body.communication,
            ownership=body.ownership,
            interview_summary=body.interview_summary,
            interview_notes=body.interview_notes,
            recommendation=body.recommendation,
        )
    except ScorecardCandidateNotFoundError:
        raise api_error(
            404, "CANDIDATE_NOT_FOUND", "Candidate not found or unavailable"
        ) from None
    except SQLAlchemyError:
        raise api_error(500, "DATABASE_ERROR", "Database operation failed") from None
    return InterviewScorecardResponse.model_validate(entry)


@router.get(
    "/matches/{candidate_id}",
    response_model=MatchDetailsResponse,
)
def get_match_details(
    candidate_id: UUID,
    vacancy_id: Annotated[UUID, Query()],
    current_user: Annotated[User, Depends(require_employer)],
    session: Annotated[Session, Depends(get_db)],
) -> MatchDetailsResponse:
    """Explainable match view for one candidate against an owned vacancy."""
    _require_owned_vacancy(session, current_user.id, vacancy_id)
    try:
        return build_match_details(session, vacancy_id=vacancy_id, candidate_id=candidate_id)
    except MatchDetailsCandidateNotFoundError:
        raise api_error(
            404, "CANDIDATE_NOT_FOUND", "Candidate not found or unavailable"
        ) from None
    except SQLAlchemyError:
        raise api_error(500, "DATABASE_ERROR", "Database operation failed") from None


@router.get(
    "/matches/{candidate_id}/interview-questions",
    response_model=InterviewQuestionsResponse,
)
def get_match_interview_questions(
    candidate_id: UUID,
    vacancy_id: Annotated[UUID, Query()],
    current_user: Annotated[User, Depends(require_employer)],
    session: Annotated[Session, Depends(get_db)],
    refresh: Annotated[bool, Query()] = False,
) -> InterviewQuestionsResponse:
    """Employer-only interview preparation questions for one match."""
    company = _require_owned_vacancy(session, current_user.id, vacancy_id)
    try:
        details = build_match_details(session, vacancy_id=vacancy_id, candidate_id=candidate_id)
    except MatchDetailsCandidateNotFoundError:
        raise api_error(
            404, "CANDIDATE_NOT_FOUND", "Candidate not found or unavailable"
        ) from None
    try:
        context = build_interview_questions_context(
            session,
            employer_id=company.id,
            vacancy_id=vacancy_id,
            candidate_id=candidate_id,
            details=details,
        )
        return get_interview_questions(context, refresh=refresh)
    except InterviewQuestionsUnavailableError:
        raise api_error(
            503,
            "INTERVIEW_QUESTIONS_UNAVAILABLE",
            "Interview questions are temporarily unavailable.",
        ) from None


@router.get(
    "/matches/{candidate_id}/ai-hiring-intelligence",
    response_model=AiHiringIntelligenceResponse,
)
def get_ai_hiring_intelligence(
    candidate_id: UUID,
    vacancy_id: Annotated[UUID, Query()],
    current_user: Annotated[User, Depends(require_employer)],
    session: Annotated[Session, Depends(get_db)],
) -> AiHiringIntelligenceResponse:
    """Employer-only interpretation of the candidate's existing evidence."""
    _require_owned_vacancy(session, current_user.id, vacancy_id)
    try:
        build_match_details(session, vacancy_id=vacancy_id, candidate_id=candidate_id)
    except MatchDetailsCandidateNotFoundError:
        raise api_error(
            404, "CANDIDATE_NOT_FOUND", "Candidate not found or unavailable"
        ) from None
    context = build_hiring_context(
        candidate_name=None,
        passport=build_passport(session, candidate_id),
    )
    try:
        return get_hiring_intelligence(context)
    except HiringIntelligenceUnavailableError:
        raise api_error(
            503, "AI_HIRING_INTELLIGENCE_UNAVAILABLE", "AI analysis is temporarily unavailable."
        ) from None


@router.post(
    "/matches/{candidate_id}/explanation",
    response_model=AiMatchExplanationResponse,
)
def post_match_explanation(
    candidate_id: UUID,
    vacancy_id: Annotated[UUID, Query()],
    current_user: Annotated[User, Depends(require_employer)],
    session: Annotated[Session, Depends(get_db)],
) -> AiMatchExplanationResponse:
    company = _require_owned_vacancy(session, current_user.id, vacancy_id)
    vacancy = get_vacancy(session, company.id, vacancy_id)
    if vacancy is None:
        raise api_error(404, "VACANCY_NOT_FOUND", "Vacancy not found")
    try:
        details = build_match_details(session, vacancy_id=vacancy_id, candidate_id=candidate_id)
    except MatchDetailsCandidateNotFoundError:
        raise api_error(
            404, "CANDIDATE_NOT_FOUND", "Candidate not found or unavailable"
        ) from None
    requirement_rows = list_vacancy_requirements(session, vacancy_id)
    explanation_input = build_explanation_input(
        details=details,
        confirmed_skills=[skill.name for skill in build_passport(session, candidate_id).skills],
        vacancy_title=vacancy.title,
        required_skills=[
            skill.canonical_name
            for requirement, skill in requirement_rows
            if requirement.requirement_type == "required"
        ],
        preferred_skills=[
            skill.canonical_name
            for requirement, skill in requirement_rows
            if requirement.requirement_type == "preferred"
        ],
    )
    try:
        return explain_match(explanation_input)
    except MatchExplanationUnavailableError:
        raise api_error(
            503, "AI_EXPLANATION_UNAVAILABLE", "AI explanation is currently unavailable."
        ) from None
