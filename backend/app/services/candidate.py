from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.candidate_profile import CandidateProfile, OnboardingStatus


class CandidateProfileNotFoundError(Exception):
    pass


def get_candidate_profile(session: Session, user_id: UUID) -> CandidateProfile | None:
    return session.execute(
        select(CandidateProfile).where(CandidateProfile.user_id == user_id)
    ).scalar_one_or_none()


def calculate_onboarding_status(_: CandidateProfile) -> OnboardingStatus:
    return OnboardingStatus.PROFILE_REQUIRED


def patch_candidate_profile(
    session: Session, user_id: UUID, patch_data: dict[str, object]
) -> CandidateProfile:
    profile = get_candidate_profile(session, user_id)
    if profile is None:
        raise CandidateProfileNotFoundError

    for field_name, value in patch_data.items():
        setattr(profile, field_name, value)
    profile.onboarding_status = calculate_onboarding_status(profile)

    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise
    session.refresh(profile)
    return profile
