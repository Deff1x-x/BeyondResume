from unittest.mock import Mock
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.api import dependencies
from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User


@pytest.fixture(autouse=True)
def configured_jwt_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "jwt_secret", "stage-3-test-secret-with-32-bytes-minimum")


def make_user(role: str = "candidate", status: str = "active") -> User:
    return User(
        id=uuid4(),
        email="user@example.com",
        password_hash="$argon2id$not-public",
        role=role,
        status=status,
    )


def test_current_active_user_loads_user_from_database(monkeypatch: pytest.MonkeyPatch) -> None:
    user = make_user()
    token = create_access_token(user.id)
    monkeypatch.setattr(dependencies, "get_user_by_id", lambda *_args: user)

    current_user = dependencies.get_current_active_user(
        HTTPAuthorizationCredentials(scheme="Bearer", credentials=token), Mock()
    )

    assert current_user is user


@pytest.mark.parametrize("user", [None, make_user(status="suspended")])
def test_unknown_or_inactive_user_is_rejected(
    user: User | None, monkeypatch: pytest.MonkeyPatch
) -> None:
    token = create_access_token(uuid4())
    monkeypatch.setattr(dependencies, "get_user_by_id", lambda *_args: user)

    with pytest.raises(HTTPException) as error:
        dependencies.get_current_active_user(
            HTTPAuthorizationCredentials(scheme="Bearer", credentials=token), Mock()
        )

    assert error.value.status_code == 401
    assert error.value.headers == {"WWW-Authenticate": "Bearer"}


def test_expired_token_is_rejected_as_unauthorized() -> None:
    token = jwt.encode(
        {"sub": str(uuid4()), "exp": datetime.now(UTC) - timedelta(seconds=1)},
        settings.jwt_secret,
        algorithm="HS256",
    )

    with pytest.raises(HTTPException) as error:
        dependencies.get_current_active_user(
            HTTPAuthorizationCredentials(scheme="Bearer", credentials=token), Mock()
        )

    assert error.value.status_code == 401
    assert error.value.headers == {"WWW-Authenticate": "Bearer"}


def test_role_dependencies_enforce_candidate_and_employer() -> None:
    candidate = make_user("candidate")
    employer = make_user("employer")

    assert dependencies.require_candidate(candidate) is candidate
    assert dependencies.require_employer(employer) is employer
    with pytest.raises(HTTPException) as candidate_error:
        dependencies.require_candidate(employer)
    with pytest.raises(HTTPException) as employer_error:
        dependencies.require_employer(candidate)

    assert candidate_error.value.status_code == 403
    assert employer_error.value.status_code == 403
