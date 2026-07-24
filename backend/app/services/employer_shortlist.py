"""Persistence services for vacancy-scoped employer shortlists."""

from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.candidate_profile import CandidateProfile
from app.models.employer_candidate_shortlist import EmployerCandidateShortlist
from app.models.vacancy import Vacancy


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
    """Idempotently save an existing candidate for an owned vacancy."""
    employer_id = vacancy.employer_id
    vacancy_id = vacancy.id

    candidate_exists = session.scalar(
        select(CandidateProfile.id).where(CandidateProfile.id == candidate_id)
    )
    if candidate_exists is None:
        raise ShortlistCandidateNotFoundError

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
    """Idempotently remove one saved candidate for an owned vacancy."""
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
    """List saved candidates newest-first for one owned vacancy."""
    return list(
        session.execute(
            select(EmployerCandidateShortlist)
            .where(
                EmployerCandidateShortlist.employer_id == vacancy.employer_id,
                EmployerCandidateShortlist.vacancy_id == vacancy.id,
            )
            .order_by(
                EmployerCandidateShortlist.created_at.desc(),
                EmployerCandidateShortlist.id.desc(),
            )
        )
        .scalars()
        .all()
    )


def update_candidate_stage(
    session: Session,
    *,
    vacancy: Vacancy,
    candidate_id: UUID,
    stage: str,
) -> EmployerCandidateShortlist:
    """Update hiring stage for an existing shortlist entry on an owned vacancy."""
    entry = session.execute(
        select(EmployerCandidateShortlist).where(
            EmployerCandidateShortlist.employer_id == vacancy.employer_id,
            EmployerCandidateShortlist.vacancy_id == vacancy.id,
            EmployerCandidateShortlist.candidate_id == candidate_id,
        )
    ).scalar_one_or_none()
    if entry is None:
        raise ShortlistEntryNotFoundError

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
