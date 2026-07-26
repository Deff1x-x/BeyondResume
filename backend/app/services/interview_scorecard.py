"""Persistence services for vacancy-scoped interview scorecards."""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.employer_interview_scorecard import EmployerInterviewScorecard
from app.models.vacancy import Vacancy
from app.services.employer_hiring_access import (
    HiringCandidateUnavailableError,
    require_interview_workflow_access,
)

SCORECARD_DIMENSIONS = (
    "technical_competency",
    "experience_relevance",
    "communication",
    "ownership",
)

DIMENSION_LABELS = {
    "technical_competency": "Technical Competency",
    "experience_relevance": "Experience Relevance",
    "communication": "Communication",
    "ownership": "Ownership",
}


class ScorecardCandidateNotFoundError(Exception):
    pass


class ScorecardNotFoundError(Exception):
    pass


class ScorecardPersistenceError(Exception):
    pass


class ScorecardValidationError(Exception):
    """Raised when a completed scorecard is missing required ratings."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def _require_interview_candidate(
    session: Session, *, vacancy: Vacancy, candidate_id: UUID
) -> None:
    try:
        require_interview_workflow_access(
            session, vacancy=vacancy, candidate_id=candidate_id
        )
    except HiringCandidateUnavailableError as error:
        raise ScorecardCandidateNotFoundError from error


def get_interview_scorecard(
    session: Session,
    *,
    vacancy: Vacancy,
    candidate_id: UUID,
) -> EmployerInterviewScorecard:
    """Load one scorecard for an owned vacancy and accessible candidate."""
    _require_interview_candidate(session, vacancy=vacancy, candidate_id=candidate_id)
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


def _validate_completed_payload(
    *,
    technical_competency: int | None,
    experience_relevance: int | None,
    communication: int | None,
    ownership: int | None,
    recommendation: str | None,
) -> None:
    missing: list[str] = []
    if technical_competency is None:
        missing.append("technical_competency")
    if experience_relevance is None:
        missing.append("experience_relevance")
    if communication is None:
        missing.append("communication")
    if ownership is None:
        missing.append("ownership")
    if recommendation is None:
        missing.append("recommendation")
    if missing:
        raise ScorecardValidationError(
            "Completed scorecards require all ratings and a recommendation"
        )


def build_scorecard_summary(entry: EmployerInterviewScorecard) -> dict[str, object]:
    """Deterministic summary derived only from employer-entered ratings."""
    rated: list[tuple[str, int]] = []
    unanswered: list[str] = []
    for key in SCORECARD_DIMENSIONS:
        value = getattr(entry, key)
        if value is None:
            unanswered.append(DIMENSION_LABELS[key])
        else:
            rated.append((DIMENSION_LABELS[key], int(value)))

    average: float | None = None
    strongest: list[str] = []
    weakest: list[str] = []
    if rated:
        average = round(sum(score for _, score in rated) / len(rated), 2)
        max_score = max(score for _, score in rated)
        min_score = min(score for _, score in rated)
        strongest = [label for label, score in rated if score == max_score]
        weakest = [label for label, score in rated if score == min_score]

    return {
        "status": entry.status,
        "completed_criteria_count": len(rated),
        "total_criteria_count": len(SCORECARD_DIMENSIONS),
        "average_rating": average,
        "strongest_dimensions": strongest,
        "weakest_dimensions": weakest,
        "unanswered_dimensions": unanswered,
        "recommendation": entry.recommendation,
    }


def upsert_interview_scorecard(
    session: Session,
    *,
    vacancy: Vacancy,
    candidate_id: UUID,
    status: str,
    technical_competency: int | None,
    experience_relevance: int | None,
    communication: int | None,
    ownership: int | None,
    interview_summary: str | None,
    interview_notes: str | None,
    recommendation: str | None,
) -> EmployerInterviewScorecard:
    """Create or replace one interview scorecard for an accessible candidate."""
    _require_interview_candidate(session, vacancy=vacancy, candidate_id=candidate_id)

    if status == "completed":
        _validate_completed_payload(
            technical_competency=technical_competency,
            experience_relevance=experience_relevance,
            communication=communication,
            ownership=ownership,
            recommendation=recommendation,
        )

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
            status=status,
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
        entry.status = status
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
