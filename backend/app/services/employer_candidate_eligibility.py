"""Shared employer-facing candidate eligibility policy.

Temporary MVP contract until a real candidate lifecycle/onboarding state exists:

eligible ⇔
- CandidateProfile exists
- linked User exists
- User.role == "candidate"
- User.status == "active"
- trimmed CandidateProfile.display_name is non-empty

``CandidateProfile.onboarding_status`` is intentionally unused: the model only
exposes ``PROFILE_REQUIRED`` and does not reflect completed onboarding.
"""

from __future__ import annotations

from uuid import UUID

from typing import Any

from sqlalchemy import ColumnElement, and_, func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.models.candidate_profile import CandidateProfile
from app.models.user import User


class EmployerCandidateUnavailableError(Exception):
    """Raised when a candidate is missing or not eligible for employer workflows."""


def candidate_has_non_empty_display_name() -> ColumnElement[bool]:
    """SQL predicate for a usable canonical display name."""
    return and_(
        CandidateProfile.display_name.is_not(None),
        func.length(func.trim(CandidateProfile.display_name)) > 0,
    )


def employer_eligible_candidate_filters() -> tuple[ColumnElement[bool], ...]:
    """Reusable WHERE predicates for employer-eligible candidates."""
    return (
        User.role == "candidate",
        User.status == "active",
        candidate_has_non_empty_display_name(),
    )


def select_employer_eligible_candidates() -> Select[Any]:
    """Base select of eligible CandidateProfile rows joined to User."""
    return (
        select(CandidateProfile)
        .join(User, User.id == CandidateProfile.user_id)
        .where(*employer_eligible_candidate_filters())
    )


def trimmed_candidate_display_name(candidate: CandidateProfile) -> str | None:
    """Return the canonical trimmed name, or None when identity is missing."""
    if candidate.display_name is None:
        return None
    name = candidate.display_name.strip()
    return name or None


def get_employer_eligible_candidate(
    session: Session, candidate_id: UUID
) -> CandidateProfile | None:
    """Return one eligible candidate profile, or None when unavailable."""
    return session.execute(
        select_employer_eligible_candidates().where(CandidateProfile.id == candidate_id)
    ).scalar_one_or_none()


def require_employer_eligible_candidate(
    session: Session, candidate_id: UUID
) -> CandidateProfile:
    """Return one eligible candidate or raise a unified unavailable error."""
    candidate = get_employer_eligible_candidate(session, candidate_id)
    if candidate is None:
        raise EmployerCandidateUnavailableError
    return candidate


def list_employer_eligible_candidates(session: Session) -> list[CandidateProfile]:
    """List all employer-eligible candidates once each, ordered by display name."""
    return list(
        session.execute(
            select_employer_eligible_candidates().order_by(
                CandidateProfile.display_name, CandidateProfile.id
            )
        )
        .scalars()
        .all()
    )
