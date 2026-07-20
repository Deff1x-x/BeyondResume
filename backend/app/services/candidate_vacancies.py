"""Candidate-facing vacancy discovery using existing deterministic services."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.employer_profile import EmployerProfile
from app.models.vacancy import Vacancy
from app.services.employer import list_vacancy_requirements
from app.services.matching import MatchRequirement, MatchResult, match_passport_to_requirements
from app.services.roadmap import build_roadmap_from_match
from app.services.skill_passport import build_passport


@dataclass(frozen=True, slots=True)
class CandidateVacancyMatch:
    vacancy: Vacancy
    company_name: str
    required_skills: tuple[str, ...]
    preferred_skills: tuple[str, ...]
    match: MatchResult


class CandidateVacancyNotFoundError(Exception):
    pass


def list_candidate_vacancies(
    session: Session, candidate_id: UUID
) -> list[CandidateVacancyMatch]:
    passport = build_passport(session, candidate_id)
    rows = session.execute(
        select(Vacancy, EmployerProfile.company_name)
        .join(EmployerProfile, EmployerProfile.id == Vacancy.employer_id)
        .where(Vacancy.status == "open")
        .order_by(Vacancy.created_at.desc())
    ).all()

    matches = [
        _build_candidate_vacancy_match(session, passport, vacancy, company_name)
        for vacancy, company_name in rows
    ]
    # Python sort is stable, preserving the database's existing created_at order on ties.
    matches.sort(key=lambda item: -item.match.score)
    return matches


def get_candidate_vacancy(
    session: Session, candidate_id: UUID, vacancy_id: UUID
) -> CandidateVacancyMatch:
    row = session.execute(
        select(Vacancy, EmployerProfile.company_name)
        .join(EmployerProfile, EmployerProfile.id == Vacancy.employer_id)
        .where(Vacancy.id == vacancy_id, Vacancy.status == "open")
    ).one_or_none()
    if row is None:
        raise CandidateVacancyNotFoundError

    vacancy, company_name = row
    return _build_candidate_vacancy_match(
        session, build_passport(session, candidate_id), vacancy, company_name
    )


def vacancy_roadmap(match: MatchResult):
    """Keep candidate vacancy detail recommendations on the shared vacancy roadmap."""
    return build_roadmap_from_match(
        required_missing=match.required.missing,
        preferred_missing=match.preferred.missing,
    )


def _build_candidate_vacancy_match(
    session: Session, passport, vacancy: Vacancy, company_name: str
) -> CandidateVacancyMatch:
    requirement_rows = list_vacancy_requirements(session, vacancy.id)
    requirements = [
        MatchRequirement(
            skill_id=skill.id,
            skill_name=skill.canonical_name,
            requirement_type=requirement.requirement_type,
        )
        for requirement, skill in requirement_rows
    ]
    match = match_passport_to_requirements(passport, requirements)
    required_skills = tuple(
        skill.canonical_name
        for requirement, skill in requirement_rows
        if requirement.requirement_type == "required"
    )
    preferred_skills = tuple(
        skill.canonical_name
        for requirement, skill in requirement_rows
        if requirement.requirement_type == "preferred"
    )
    return CandidateVacancyMatch(
        vacancy=vacancy,
        company_name=company_name,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        match=match,
    )
