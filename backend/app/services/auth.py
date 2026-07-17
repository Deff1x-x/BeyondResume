from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User


class DuplicateEmailError(Exception):
    pass


def get_user_by_email(session: Session, email: str) -> User | None:
    return session.execute(select(User).where(User.email == email)).scalar_one_or_none()


def get_user_by_id(session: Session, user_id: UUID) -> User | None:
    return session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()


def register_user(session: Session, email: str, password: str, role: str) -> User:
    if get_user_by_email(session, email) is not None:
        raise DuplicateEmailError

    user = User(email=email, password_hash=hash_password(password), role=role, status="active")
    session.add(user)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise DuplicateEmailError from error

    session.refresh(user)
    return user


def authenticate_user(session: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(session, email)
    if user is None or not verify_password(password, user.password_hash):
        return None
    if user.status != "active":
        return None
    return user
