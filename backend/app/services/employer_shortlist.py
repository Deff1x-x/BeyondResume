"""Persistence services for vacancy-scoped employer shortlists."""

from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.candidate_profile import CandidateProfile
from app.models.employer_candidate_shortlist import EmployerCandidateShortlist
from app.models.user import User
from app.models.vacancy import Vacancy
from app.services.employer_candidate_eligibility import (
    EmployerCandidateUnavailableError,
    employer_eligible_candidate_filters,
    require_employer_eligible_candidate,
)


class ShortlistCandidateNotFoundError(Exception):
    pass


class ShortlistEntryNotFoundError(Exception):
    pass


class ShortlistPersistenceError(Exception):
    pass


def save_candidate_to_shortlist(
    session: Session,
    *,
    vacancy: Vacancy,
    candidate_id: UUID,
) -> EmployerCandidateShortlist:
    """Idempotently save an employer-eligible candidate for an owned vacancy."""
    employer_id = vacancy.employer_id
    vacancy_id = vacancy.id

    try:
        require_employer_eligible_candidate(session, candidate_id)
    except EmployerCandidateUnavailableError as error:
        raise ShortlistCandidateNotFoundError from error

    statement = (
        insert(EmployerCandidateShortlist)
        .values(
            id=uuid4(),
            employer_id=employer_id,
            vacancy_id=vacancy_id,
            candidate_id=candidate_id,
        )
        .on_conflict_do_nothing(
            constraint="uq_employer_candidate_shortlists_vacancy_candidate"
        )
    )
    try:
        session.execute(statement)
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise

    entry = session.execute(
        select(EmployerCandidateShortlist).where(
            EmployerCandidateShortlist.employer_id == employer_id,
            EmployerCandidateShortlist.vacancy_id == vacancy_id,
            EmployerCandidateShortlist.candidate_id == candidate_id,
        )
    ).scalar_one_or_none()
    if entry is None:
        raise ShortlistPersistenceError
    return entry


def remove_candidate_from_shortlist(
    session: Session,
    *,
    vacancy: Vacancy,
    candidate_id: UUID,
) -> None:
    """Idempotently remove one saved candidate for an owned vacancy.

    Candidate eligibility is intentionally not required so employers can clear
    stale shortlist rows for incomplete or inactive candidates.
    """
    try:
        session.execute(
            delete(EmployerCandidateShortlist).where(
                EmployerCandidateShortlist.employer_id == vacancy.employer_id,
                EmployerCandidateShortlist.vacancy_id == vacancy.id,
                EmployerCandidateShortlist.candidate_id == candidate_id,
            )
        )
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise


def list_shortlisted_candidates(
    session: Session,
    *,
    vacancy: Vacancy,
) -> list[EmployerCandidateShortlist]:
    """List eligible saved candidates newest-first for one owned vacancy.

    Persisted ineligible rows are soft-filtered and left in the database.
    """
    return list(
        session.execute(
            select(EmployerCandidateShortlist)
            .join(
                CandidateProfile,
                CandidateProfile.id == EmployerCandidateShortlist.candidate_id,
            )
            .join(User, User.id == CandidateProfile.user_id)
            .where(
                EmployerCandidateShortlist.employer_id == vacancy.employer_id,
                EmployerCandidateShortlist.vacancy_id == vacancy.id,
                *employer_eligible_candidate_filters(),
            )
            .order_by(
                EmployerCandidateShortlist.created_at.desc(),
                EmployerCandidateShortlist.id.desc(),
            )
        )
        .scalars()
        .all()
    )


def _require_owned_shortlist_entry(
    session: Session,
    *,
    vacancy: Vacancy,
    candidate_id: UUID,
) -> EmployerCandidateShortlist:
    entry = session.execute(
        select(EmployerCandidateShortlist).where(
            EmployerCandidateShortlist.employer_id == vacancy.employer_id,
            EmployerCandidateShortlist.vacancy_id == vacancy.id,
            EmployerCandidateShortlist.candidate_id == candidate_id,
        )
    ).scalar_one_or_none()
    if entry is None:
        raise ShortlistEntryNotFoundError
    return entry


def update_candidate_stage(
    session: Session,
    *,
    vacancy: Vacancy,
    candidate_id: UUID,
    stage: str,
) -> EmployerCandidateShortlist:
    """Update hiring stage for an eligible shortlist entry on an owned vacancy."""
    entry = _require_owned_shortlist_entry(
        session, vacancy=vacancy, candidate_id=candidate_id
    )
    try:
        require_employer_eligible_candidate(session, candidate_id)
    except EmployerCandidateUnavailableError as error:
        raise ShortlistCandidateNotFoundError from error

    if entry.stage == stage:
        return entry

    entry.stage = stage
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise
    session.refresh(entry)
    return entry


def update_candidate_note(
    session: Session,
    *,
    vacancy: Vacancy,
    candidate_id: UUID,
    note: str | None,
) -> EmployerCandidateShortlist:
    """Update private employer note for an eligible shortlist entry."""
    entry = _require_owned_shortlist_entry(
        session, vacancy=vacancy, candidate_id=candidate_id
    )
    try:
        require_employer_eligible_candidate(session, candidate_id)
    except EmployerCandidateUnavailableError as error:
        raise ShortlistCandidateNotFoundError from error

    if entry.note == note:
        return entry

    entry.note = note
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise
    session.refresh(entry)
    return entry
