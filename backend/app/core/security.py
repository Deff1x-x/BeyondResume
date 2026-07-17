from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from argon2.low_level import Type
from jwt import InvalidTokenError

from app.core.config import settings

JWT_ALGORITHM = "HS256"
_password_hasher = PasswordHasher(type=Type.ID)


def hash_password(plain_password: str) -> str:
    return _password_hasher.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, plain_password)
    except (InvalidHashError, VerificationError):
        return False


def create_access_token(user_id: UUID) -> str:
    if not settings.jwt_secret:
        raise RuntimeError("JWT_SECRET must be configured")

    expires_at = datetime.now(UTC) + timedelta(minutes=settings.jwt_access_ttl_minutes)
    return jwt.encode(
        {"sub": str(user_id), "exp": expires_at},
        settings.jwt_secret,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> UUID:
    if not settings.jwt_secret:
        raise InvalidTokenError("JWT secret is not configured")

    payload = jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALGORITHM])
    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise InvalidTokenError("Token subject is invalid")

    try:
        return UUID(subject)
    except ValueError as error:
        raise InvalidTokenError("Token subject is invalid") from error
