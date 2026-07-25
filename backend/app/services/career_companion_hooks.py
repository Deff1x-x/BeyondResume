"""Quiet helper to refresh Career Companion after evidence sync."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def maybe_refresh_companion_after_evidence(session: Session, candidate_id: UUID) -> None:
    """Refresh companion verification in an isolated session.

    Uses a separate DB session so companion commit/rollback never interferes with
    the caller's GitHub-scan or resume-parse transaction, and companion errors
    cannot fail the primary ingestion path.
    """
    del session  # caller session intentionally unused — isolation required
    from app.db.session import SessionLocal
    from app.services.career_companion.verification import refresh_plan_from_evidence

    companion_session = SessionLocal()
    try:
        refresh_plan_from_evidence(companion_session, candidate_id)
    except Exception:
        logger.exception(
            "Career Companion evidence refresh failed for candidate %s", candidate_id
        )
        companion_session.rollback()
    finally:
        companion_session.close()
