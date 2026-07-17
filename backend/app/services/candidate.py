from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.candidate_profile import CandidateProfile


class MissingCandidateProfileFullNameError(Exception):
    pass


def get_candidate_profile(session: Session, user_id: UUID) -> CandidateProfile | None:
    return session.execute(
        select(CandidateProfile).where(CandidateProfile.user_id == user_id)
    ).scalar_one_or_none()


def patch_candidate_profile(
    session: Session, user_id: UUID, patch_data: dict[str, object]
) -> CandidateProfile:
    profile = get_candidate_profile(session, user_id)
    if profile is None:
        full_name = patch_data.get("full_name")
        if not isinstance(full_name, str):
            raise MissingCandidateProfileFullNameError
        profile = CandidateProfile(user_id=user_id, **patch_data)
        session.add(profile)
    else:
        for field_name, value in patch_data.items():
            setattr(profile, field_name, value)

    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise
    session.refresh(profile)
    return profile
