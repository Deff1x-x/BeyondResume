from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.audit_event import AuditEvent
from app.models.candidate_profile import CandidateProfile
from app.models.user import User


class DuplicateEmailError(Exception):
    pass


class PasswordPolicyError(Exception):
    pass


class RegistrationPersistenceError(Exception):
    pass


def normalize_email(email: str) -> str:
    return email.strip().lower()


def get_user_by_email(session: Session, email: str) -> User | None:
    return session.execute(select(User).where(User.email == email)).scalar_one_or_none()


def get_user_by_id(session: Session, user_id: UUID) -> User | None:
    return session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()


def create_empty_candidate_profile(user_id: UUID) -> CandidateProfile:
    return CandidateProfile(user_id=user_id, full_name="", onboarding_status="profile_required")


def create_user_registered_audit_event(user_id: UUID) -> AuditEvent:
    return AuditEvent(user_id=user_id, event_type="user_registered")


def register_user(
    session: Session, email: str, password: str, role: str, *, demo_mode: bool = True
) -> User:
    email = normalize_email(email)
    if get_user_by_email(session, email) is not None:
        raise DuplicateEmailError

    account_status = "active" if demo_mode else "pending_verification"
    user = User(
        id=uuid4(),
        email=email,
        password_hash=hash_password(password),
        role=role,
        status=account_status,
    )
    try:
        session.add(user)
        if role == "candidate":
            session.add(create_empty_candidate_profile(user.id))
        session.add(create_user_registered_audit_event(user.id))
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise DuplicateEmailError from error
    except Exception as error:
        session.rollback()
        raise RegistrationPersistenceError from error

    return user


def authenticate_user(session: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(session, normalize_email(email))
    if user is None or not verify_password(password, user.password_hash):
        return None
    if user.status != "active":
        return None
    return user


def validate_registration_password(password: str, password_confirmation: str) -> None:
    if len(password) < 8 or password != password_confirmation:
        raise PasswordPolicyError
