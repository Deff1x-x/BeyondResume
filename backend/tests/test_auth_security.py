from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from jwt import InvalidTokenError

from app.core.config import settings
from app.core.security import (
    JWT_ALGORITHM,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


@pytest.fixture(autouse=True)
def configured_jwt_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "jwt_secret", "stage-3-test-secret-with-32-bytes-minimum")
    monkeypatch.setattr(settings, "jwt_access_ttl_minutes", 15)


def test_password_hash_is_argon2id_and_verifies() -> None:
    password_hash = hash_password("StrongPass123")
    assert password_hash != "StrongPass123"
    assert password_hash.startswith("$argon2id$")
    assert verify_password("StrongPass123", password_hash)
    assert not verify_password("WrongPass123", password_hash)


def test_invalid_hash_returns_false() -> None:
    assert not verify_password("StrongPass123", "invalid-hash")


def test_access_token_contains_subject_and_expiration() -> None:
    user_id = uuid4()
    token = create_access_token(user_id)
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALGORITHM])
    assert payload["sub"] == str(user_id)
    assert datetime.fromtimestamp(payload["exp"], UTC) > datetime.now(UTC) + timedelta(minutes=14)


def test_expired_and_malformed_tokens_are_rejected() -> None:
    expired_token = jwt.encode(
        {"sub": str(uuid4()), "exp": datetime.now(UTC) - timedelta(seconds=1)},
        settings.jwt_secret,
        algorithm=JWT_ALGORITHM,
    )
    with pytest.raises(InvalidTokenError):
        decode_access_token(expired_token)
    with pytest.raises(InvalidTokenError):
        decode_access_token("not-a-jwt")
