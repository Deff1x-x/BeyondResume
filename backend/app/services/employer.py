"""Employer company (EmployerProfile) and vacancy services."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.candidate_profile import CandidateProfile
from app.models.employer_candidate_shortlist import EmployerCandidateShortlist
from app.models.employer_interview_scorecard import EmployerInterviewScorecard
from app.models.employer_profile import EmployerProfile
from app.models.skill import Skill
from app.models.vacancy import Vacancy
from app.models.vacancy_skill_requirement import VacancySkillRequirement
from app.services.employer_candidate_eligibility import (
    list_employer_eligible_candidates,
    trimmed_candidate_display_name,
)
from app.services.matching import MatchRequirement, MatchResult, match_passport_to_requirements
from app.services.skill_passport import build_passport


class EmployerCompanyNotFoundError(Exception):
    pass


class EmployerCompanyAlreadyExistsError(Exception):
    pass


class VacancyNotFoundError(Exception):
    pass


class SkillNotAvailableError(Exception):
    pass


class VacancyRequirementConflictError(Exception):
    pass


class VacancyRequirementNotFoundError(Exception):
    pass


def get_employer_company(session: Session, user_id: UUID) -> EmployerProfile | None:
    return session.execute(
        select(EmployerProfile).where(EmployerProfile.user_id == user_id)
    ).scalar_one_or_none()


def create_employer_company(
    session: Session,
    user_id: UUID,
    *,
    company_name: str,
    website: str | None,
    description: str | None,
) -> EmployerProfile:
    if get_employer_company(session, user_id) is not None:
        raise EmployerCompanyAlreadyExistsError

    company = EmployerProfile(
        user_id=user_id,
        company_name=company_name,
        website=website,
        description=description,
    )
    session.add(company)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise EmployerCompanyAlreadyExistsError from error
    except SQLAlchemyError:
        session.rollback()
        raise
    session.refresh(company)
    return company


def update_employer_company(
    session: Session,
    user_id: UUID,
    *,
    company_name: str | None = None,
    website: str | None = None,
    description: str | None = None,
    website_set: bool = False,
    description_set: bool = False,
) -> EmployerProfile:
    """Update the authenticated employer's company. Foreign/missing company → not found."""
    company = get_employer_company(session, user_id)
    if company is None:
        raise EmployerCompanyNotFoundError

    if company_name is not None:
        company.company_name = company_name
    if website_set:
        company.website = website
    if description_set:
        company.description = description

    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise
    session.refresh(company)
    return company


def list_vacancies(session: Session, employer_id: UUID) -> list[Vacancy]:
    return list(
        session.execute(
            select(Vacancy)
            .where(Vacancy.employer_id == employer_id)
            .order_by(Vacancy.created_at.desc())
        )
        .scalars()
        .all()
    )


def get_vacancy(session: Session, employer_id: UUID, vacancy_id: UUID) -> Vacancy | None:
    return session.execute(
        select(Vacancy).where(Vacancy.id == vacancy_id, Vacancy.employer_id == employer_id)
    ).scalar_one_or_none()


def create_vacancy(
    session: Session,
    employer_id: UUID,
    *,
    title: str,
    description: str | None,
    status: str,
) -> Vacancy:
    vacancy = Vacancy(
        employer_id=employer_id,
        title=title,
        description=description,
        status=status,
    )
    session.add(vacancy)
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise
    session.refresh(vacancy)
    return vacancy


def delete_vacancy(session: Session, employer_id: UUID, vacancy_id: UUID) -> None:
    """Delete an owned vacancy and vacancy-scoped dependents in one transaction.

    FK constraints on vacancy children use NO ACTION (no CASCADE). Related rows
    owned by the vacancy are removed explicitly; users, candidates, skills, and
    other global entities are never deleted.
    """
    vacancy = get_vacancy(session, employer_id, vacancy_id)
    if vacancy is None:
        raise VacancyNotFoundError

    try:
        session.execute(
            delete(EmployerInterviewScorecard).where(
                EmployerInterviewScorecard.vacancy_id == vacancy_id
            )
        )
        session.execute(
            delete(EmployerCandidateShortlist).where(
                EmployerCandidateShortlist.vacancy_id == vacancy_id
            )
        )
        session.execute(
            delete(VacancySkillRequirement).where(
                VacancySkillRequirement.vacancy_id == vacancy_id
            )
        )
        session.delete(vacancy)
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise


def list_available_skills(session: Session) -> list[Skill]:
    return list(
        session.execute(
            select(Skill)
            .where(Skill.deprecated.is_(False))
            .order_by(Skill.canonical_name)
        )
        .scalars()
        .all()
    )


def list_vacancy_requirements(
    session: Session, vacancy_id: UUID
) -> list[tuple[VacancySkillRequirement, Skill]]:
    rows = session.execute(
        select(VacancySkillRequirement, Skill)
        .join(Skill, Skill.id == VacancySkillRequirement.skill_id)
        .where(VacancySkillRequirement.vacancy_id == vacancy_id)
        .order_by(
            VacancySkillRequirement.requirement_type,
            Skill.canonical_name,
        )
    ).all()
    return [(requirement, skill) for requirement, skill in rows]


def add_vacancy_requirement(
    session: Session,
    vacancy_id: UUID,
    *,
    skill_id: UUID,
    requirement_type: str,
) -> tuple[VacancySkillRequirement, Skill]:
    skill = session.execute(
        select(Skill).where(Skill.id == skill_id, Skill.deprecated.is_(False))
    ).scalar_one_or_none()
    if skill is None:
        raise SkillNotAvailableError

    requirement = VacancySkillRequirement(
        vacancy_id=vacancy_id,
        skill_id=skill.id,
        requirement_type=requirement_type,
    )
    session.add(requirement)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise VacancyRequirementConflictError from error
    except SQLAlchemyError:
        session.rollback()
        raise
    session.refresh(requirement)
    return requirement, skill


def delete_vacancy_requirement(
    session: Session, vacancy_id: UUID, requirement_id: UUID
) -> None:
    requirement = session.execute(
        select(VacancySkillRequirement).where(
            VacancySkillRequirement.id == requirement_id,
            VacancySkillRequirement.vacancy_id == vacancy_id,
        )
    ).scalar_one_or_none()
    if requirement is None:
        raise VacancyRequirementNotFoundError
    session.delete(requirement)
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise


@dataclass(frozen=True, slots=True)
class VacancyCandidateMatch:
    candidate_id: UUID
    candidate_name: str
    result: MatchResult


def list_matchable_candidate_profiles(session: Session) -> list[CandidateProfile]:
    """Compatibility wrapper over the shared employer eligibility policy."""
    return list_employer_eligible_candidates(session)


def list_vacancy_matches(session: Session, vacancy_id: UUID) -> list[VacancyCandidateMatch]:
    """Match eligible candidate passports against this vacancy's structured requirements."""
    requirement_rows = list_vacancy_requirements(session, vacancy_id)
    requirements = [
        MatchRequirement(
            skill_id=skill.id,
            skill_name=skill.canonical_name,
            requirement_type=requirement.requirement_type,
        )
        for requirement, skill in requirement_rows
    ]

    matches: list[VacancyCandidateMatch] = []
    for candidate in list_employer_eligible_candidates(session):
        passport = build_passport(session, candidate.id)
        result = match_passport_to_requirements(passport, requirements)
        name = trimmed_candidate_display_name(candidate)
        if name is None:
            # Defensive: eligibility already requires a non-empty name.
            continue
        matches.append(
            VacancyCandidateMatch(
                candidate_id=candidate.id,
                candidate_name=name,
                result=result,
            )
        )

    matches.sort(key=lambda item: (-item.result.score, item.candidate_name.lower()))
    return matches
