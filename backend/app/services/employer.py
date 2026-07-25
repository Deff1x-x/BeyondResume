"""Employer company (EmployerProfile) and vacancy services."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.candidate_profile import CandidateProfile
from app.models.employer_profile import EmployerProfile
from app.models.skill import Skill
from app.models.user import User
from app.models.vacancy import Vacancy
from app.models.vacancy_skill_requirement import VacancySkillRequirement
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


def _candidate_display_name(candidate: CandidateProfile) -> str | None:
    """Return the canonical trimmed candidate name, or None when identity is missing."""
    if candidate.display_name is None:
        return None
    name = candidate.display_name.strip()
    return name or None


def list_matchable_candidate_profiles(session: Session) -> list[CandidateProfile]:
    """Return active candidate profiles that are eligible for employer matching.

    Empty registration shells (no display name) are excluded. Named candidates with a
    0% skill match remain eligible. Each profile is returned at most once.
    """
    return list(
        session.execute(
            select(CandidateProfile)
            .join(User, User.id == CandidateProfile.user_id)
            .where(
                User.role == "candidate",
                User.status == "active",
                and_(
                    CandidateProfile.display_name.is_not(None),
                    func.length(func.trim(CandidateProfile.display_name)) > 0,
                ),
            )
            .order_by(CandidateProfile.display_name, CandidateProfile.id)
        )
        .scalars()
        .all()
    )


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
    for candidate in list_matchable_candidate_profiles(session):
        passport = build_passport(session, candidate.id)
        result = match_passport_to_requirements(passport, requirements)
        name = _candidate_display_name(candidate)
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
