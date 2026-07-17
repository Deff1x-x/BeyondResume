from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.api.errors import api_error
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.services.auth import get_user_by_id

bearer_scheme = HTTPBearer(auto_error=False)
_bearer_header = {"WWW-Authenticate": "Bearer"}


def get_current_active_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise api_error(401, "UNAUTHORIZED", "Authentication required", headers=_bearer_header)

    try:
        user_id = decode_access_token(credentials.credentials)
    except InvalidTokenError:
        raise api_error(
            401, "UNAUTHORIZED", "Invalid access token", headers=_bearer_header
        ) from None

    user = get_user_by_id(session, user_id)
    if user is None or user.status != "active":
        raise api_error(401, "UNAUTHORIZED", "Invalid access token", headers=_bearer_header)
    return user


def require_candidate(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    if current_user.role != "candidate":
        raise api_error(403, "FORBIDDEN", "Candidate role required")
    return current_user


def require_employer(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    if current_user.role != "employer":
        raise api_error(403, "FORBIDDEN", "Employer role required")
    return current_user
