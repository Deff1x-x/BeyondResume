"""Employer-facing applicant listing, contact projection, and authorization."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.candidate_profile import CandidateProfile
from app.models.user import User
from app.models.vacancy import Vacancy
from app.services.candidate_applications import ACTIVE_APPLICATION_STATUS
from app.services.employer import list_vacancy_requirements
from app.services.employer_candidate_eligibility import (
    employer_eligible_candidate_filters,
    trimmed_candidate_display_name,
)
from app.services.matching import MatchRequirement, MatchResult, match_passport_to_requirements
from app.services.skill_passport import build_passport


class ApplicantNotFoundError(Exception):
    """Raised when no active application exists for the owned vacancy."""


@dataclass(frozen=True, slots=True)
class VacancyApplicant:
    application: Application
    candidate: CandidateProfile
    candidate_name: str
    result: MatchResult


@dataclass(frozen=True, slots=True)
class ApplicantContact:
    email: str
    phone: str | None
    telegram: str | None
    linkedin_url: str | None
    portfolio_url: str | None
    location: str | None


def get_active_application(
    session: Session, *, vacancy_id: UUID, candidate_id: UUID
) -> Application | None:
    return session.execute(
        select(Application).where(
            Application.vacancy_id == vacancy_id,
            Application.candidate_id == candidate_id,
            Application.status == ACTIVE_APPLICATION_STATUS,
        )
    ).scalar_one_or_none()


def require_active_application(
    session: Session, *, vacancy: Vacancy, candidate_id: UUID
) -> Application:
    """Authorize employer access to applicant-only workflows for one candidate."""
    application = get_active_application(
        session, vacancy_id=vacancy.id, candidate_id=candidate_id
    )
    if application is None:
        raise ApplicantNotFoundError
    return application


def list_vacancy_applicants(session: Session, *, vacancy: Vacancy) -> list[VacancyApplicant]:
    """List active eligible applicants for an owned vacancy, newest application first."""
    rows = session.execute(
        select(Application, CandidateProfile)
        .join(CandidateProfile, CandidateProfile.id == Application.candidate_id)
        .join(User, User.id == CandidateProfile.user_id)
        .where(
            Application.vacancy_id == vacancy.id,
            Application.status == ACTIVE_APPLICATION_STATUS,
            *employer_eligible_candidate_filters(),
        )
        .order_by(Application.created_at.desc(), Application.id.desc())
    ).all()

    requirement_rows = list_vacancy_requirements(session, vacancy.id)
    requirements = [
        MatchRequirement(
            skill_id=skill.id,
            skill_name=skill.canonical_name,
            requirement_type=requirement.requirement_type,
        )
        for requirement, skill in requirement_rows
    ]

    applicants: list[VacancyApplicant] = []
    for application, candidate in rows:
        name = trimmed_candidate_display_name(candidate)
        if name is None:
            continue
        passport = build_passport(session, candidate.id)
        result = match_passport_to_requirements(passport, requirements)
        applicants.append(
            VacancyApplicant(
                application=application,
                candidate=candidate,
                candidate_name=name,
                result=result,
            )
        )
    return applicants


def get_applicant_contact(
    session: Session, *, vacancy: Vacancy, candidate_id: UUID
) -> ApplicantContact:
    """Return contact fields only when an active application exists for the vacancy."""
    require_active_application(session, vacancy=vacancy, candidate_id=candidate_id)

    row = session.execute(
        select(CandidateProfile, User)
        .join(User, User.id == CandidateProfile.user_id)
        .where(
            CandidateProfile.id == candidate_id,
            *employer_eligible_candidate_filters(),
        )
    ).one_or_none()
    if row is None:
        raise ApplicantNotFoundError

    candidate, user = row
    return ApplicantContact(
        email=str(user.email),
        phone=candidate.phone,
        telegram=candidate.telegram,
        linkedin_url=candidate.linkedin_url,
        portfolio_url=candidate.portfolio_url,
        location=candidate.location,
    )
