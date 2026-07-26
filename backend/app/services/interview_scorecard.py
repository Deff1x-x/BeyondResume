"""Persistence services for vacancy-scoped interview scorecards."""

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.employer_interview_scorecard import EmployerInterviewScorecard
from app.models.vacancy import Vacancy
from app.services.employer_applications import (
    ApplicantNotFoundError,
    require_active_application,
)
from app.services.employer_candidate_eligibility import (
    EmployerCandidateUnavailableError,
    require_employer_eligible_candidate,
)


class ScorecardCandidateNotFoundError(Exception):
    pass


class ScorecardNotFoundError(Exception):
    pass


class ScorecardPersistenceError(Exception):
    pass


def _require_applicant_candidate(
    session: Session, *, vacancy: Vacancy, candidate_id: UUID
) -> None:
    try:
        require_employer_eligible_candidate(session, candidate_id)
        require_active_application(session, vacancy=vacancy, candidate_id=candidate_id)
    except (EmployerCandidateUnavailableError, ApplicantNotFoundError) as error:
        raise ScorecardCandidateNotFoundError from error


def get_interview_scorecard(
    session: Session,
    *,
    vacancy: Vacancy,
    candidate_id: UUID,
) -> EmployerInterviewScorecard:
    """Load one scorecard for an owned vacancy and active applicant."""
    _require_applicant_candidate(session, vacancy=vacancy, candidate_id=candidate_id)
    entry = session.execute(
        select(EmployerInterviewScorecard).where(
            EmployerInterviewScorecard.employer_id == vacancy.employer_id,
            EmployerInterviewScorecard.vacancy_id == vacancy.id,
            EmployerInterviewScorecard.candidate_id == candidate_id,
        )
    ).scalar_one_or_none()
    if entry is None:
        raise ScorecardNotFoundError
    return entry


def upsert_interview_scorecard(
    session: Session,
    *,
    vacancy: Vacancy,
    candidate_id: UUID,
    technical_competency: int,
    experience_relevance: int,
    communication: int,
    ownership: int,
    interview_summary: str | None,
    interview_notes: str | None,
    recommendation: str,
) -> EmployerInterviewScorecard:
    """Create or fully replace one interview scorecard for an active applicant."""
    _require_applicant_candidate(session, vacancy=vacancy, candidate_id=candidate_id)

    entry = session.execute(
        select(EmployerInterviewScorecard).where(
            EmployerInterviewScorecard.employer_id == vacancy.employer_id,
            EmployerInterviewScorecard.vacancy_id == vacancy.id,
            EmployerInterviewScorecard.candidate_id == candidate_id,
        )
    ).scalar_one_or_none()

    if entry is None:
        entry = EmployerInterviewScorecard(
            id=uuid4(),
            employer_id=vacancy.employer_id,
            vacancy_id=vacancy.id,
            candidate_id=candidate_id,
            technical_competency=technical_competency,
            experience_relevance=experience_relevance,
            communication=communication,
            ownership=ownership,
            interview_summary=interview_summary,
            interview_notes=interview_notes,
            recommendation=recommendation,
        )
        session.add(entry)
    else:
        entry.technical_competency = technical_competency
        entry.experience_relevance = experience_relevance
        entry.communication = communication
        entry.ownership = ownership
        entry.interview_summary = interview_summary
        entry.interview_notes = interview_notes
        entry.recommendation = recommendation

    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise
    session.refresh(entry)
    return entry
