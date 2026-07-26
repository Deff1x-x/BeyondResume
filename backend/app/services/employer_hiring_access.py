"""Shared employer hiring-access policy for shortlist, questions, and scorecards.

Access rules (server-side ownership of the vacancy is enforced by callers):

- Shortlist save/update: employer-eligible candidate.
- Interview questions / scorecard: employer-eligible candidate who either
  has an active application for the vacancy or is already shortlisted for it.

Match Score and recommended-candidate listing remain separate; this module does
not change deterministic matching.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.employer_candidate_shortlist import EmployerCandidateShortlist
from app.models.vacancy import Vacancy
from app.services.employer_applications import get_active_application
from app.services.employer_candidate_eligibility import (
    EmployerCandidateUnavailableError,
    require_employer_eligible_candidate,
)


class HiringCandidateUnavailableError(Exception):
    """Raised when a candidate cannot be used in hiring workflows."""


def is_shortlisted(
    session: Session, *, vacancy: Vacancy, candidate_id: UUID
) -> bool:
    return (
        session.execute(
            select(EmployerCandidateShortlist.id).where(
                EmployerCandidateShortlist.employer_id == vacancy.employer_id,
                EmployerCandidateShortlist.vacancy_id == vacancy.id,
                EmployerCandidateShortlist.candidate_id == candidate_id,
            )
        ).scalar_one_or_none()
        is not None
    )


def require_shortlist_eligible_candidate(
    session: Session, *, vacancy: Vacancy, candidate_id: UUID
) -> None:
    """Authorize shortlist mutations for an eligible candidate on an owned vacancy."""
    del vacancy  # Ownership is enforced by the caller via the Vacancy row.
    try:
        require_employer_eligible_candidate(session, candidate_id)
    except EmployerCandidateUnavailableError as error:
        raise HiringCandidateUnavailableError from error


def require_interview_workflow_access(
    session: Session, *, vacancy: Vacancy, candidate_id: UUID
) -> None:
    """Authorize interview questions / scorecard for applicants or shortlisted candidates."""
    try:
        require_employer_eligible_candidate(session, candidate_id)
    except EmployerCandidateUnavailableError as error:
        raise HiringCandidateUnavailableError from error

    application = get_active_application(
        session, vacancy_id=vacancy.id, candidate_id=candidate_id
    )
    if application is not None:
        return
    if is_shortlisted(session, vacancy=vacancy, candidate_id=candidate_id):
        return
    raise HiringCandidateUnavailableError
