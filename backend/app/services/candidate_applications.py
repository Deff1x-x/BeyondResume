"""Candidate apply / withdraw services for vacancy applications."""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.vacancy import Vacancy

ACTIVE_APPLICATION_STATUS = "applied"
WITHDRAWN_APPLICATION_STATUS = "withdrawn"


class ApplicationVacancyNotFoundError(Exception):
    """Vacancy is missing or not open for applications."""


class ApplicationNotFoundError(Exception):
    """No application exists for this candidate and vacancy."""


class ApplicationPersistenceError(Exception):
    """Application row could not be persisted or reloaded."""


def get_open_vacancy(session: Session, vacancy_id: UUID) -> Vacancy | None:
    return session.execute(
        select(Vacancy).where(Vacancy.id == vacancy_id, Vacancy.status == "open")
    ).scalar_one_or_none()


def get_application(
    session: Session, *, vacancy_id: UUID, candidate_id: UUID
) -> Application | None:
    return session.execute(
        select(Application).where(
            Application.vacancy_id == vacancy_id,
            Application.candidate_id == candidate_id,
        )
    ).scalar_one_or_none()


def map_applications_for_candidate(
    session: Session, *, candidate_id: UUID, vacancy_ids: list[UUID]
) -> dict[UUID, Application]:
    """Bulk-load application rows for one candidate across many vacancies."""
    if not vacancy_ids:
        return {}
    rows = session.execute(
        select(Application).where(
            Application.candidate_id == candidate_id,
            Application.vacancy_id.in_(vacancy_ids),
        )
    ).scalars().all()
    return {row.vacancy_id: row for row in rows}


def apply_to_vacancy(
    session: Session, *, vacancy_id: UUID, candidate_id: UUID
) -> Application:
    """Create or reactivate an application as ``applied`` for an open vacancy."""
    vacancy = get_open_vacancy(session, vacancy_id)
    if vacancy is None:
        raise ApplicationVacancyNotFoundError

    existing = get_application(
        session, vacancy_id=vacancy_id, candidate_id=candidate_id
    )
    if existing is not None:
        if existing.status != ACTIVE_APPLICATION_STATUS:
            existing.status = ACTIVE_APPLICATION_STATUS
            try:
                session.commit()
            except SQLAlchemyError:
                session.rollback()
                raise
            session.refresh(existing)
        return existing

    statement = (
        insert(Application)
        .values(
            id=uuid4(),
            vacancy_id=vacancy_id,
            candidate_id=candidate_id,
            status=ACTIVE_APPLICATION_STATUS,
        )
        .on_conflict_do_nothing(constraint="uq_applications_vacancy_candidate")
    )
    try:
        session.execute(statement)
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise

    entry = get_application(session, vacancy_id=vacancy_id, candidate_id=candidate_id)
    if entry is None:
        raise ApplicationPersistenceError
    if entry.status != ACTIVE_APPLICATION_STATUS:
        entry.status = ACTIVE_APPLICATION_STATUS
        try:
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
        session.refresh(entry)
    return entry


def withdraw_application(
    session: Session, *, vacancy_id: UUID, candidate_id: UUID
) -> Application:
    """Mark an existing application as withdrawn (idempotent when already withdrawn)."""
    vacancy = get_open_vacancy(session, vacancy_id)
    if vacancy is None:
        # Allow withdraw against closed vacancies if the application already exists.
        vacancy_exists = session.execute(
            select(Vacancy.id).where(Vacancy.id == vacancy_id)
        ).scalar_one_or_none()
        if vacancy_exists is None:
            raise ApplicationVacancyNotFoundError

    entry = get_application(session, vacancy_id=vacancy_id, candidate_id=candidate_id)
    if entry is None:
        raise ApplicationNotFoundError

    if entry.status == WITHDRAWN_APPLICATION_STATUS:
        return entry

    entry.status = WITHDRAWN_APPLICATION_STATUS
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise
    session.refresh(entry)
    return entry


def has_active_application(
    session: Session, *, vacancy_id: UUID, candidate_id: UUID
) -> bool:
    entry = session.execute(
        select(Application.id).where(
            Application.vacancy_id == vacancy_id,
            Application.candidate_id == candidate_id,
            Application.status == ACTIVE_APPLICATION_STATUS,
        )
    ).scalar_one_or_none()
    return entry is not None
