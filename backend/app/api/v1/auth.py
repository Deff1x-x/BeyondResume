from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.errors import api_error
from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    VerificationRequiredResponse,
)
from app.services.auth import (
    DuplicateEmailError,
    PasswordPolicyError,
    RegistrationPersistenceError,
    authenticate_user,
    register_user,
    validate_registration_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenResponse | VerificationRequiredResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: RegisterRequest,
    session: Annotated[Session, Depends(get_db)],
) -> TokenResponse | VerificationRequiredResponse:
    if not payload.terms_accepted or not payload.privacy_accepted:
        raise api_error(422, "CONSENT_REQUIRED", "Terms and Privacy consent are required")

    try:
        validate_registration_password(payload.password, payload.password_confirmation)
    except PasswordPolicyError:
        raise api_error(
            422, "PASSWORD_POLICY_FAILED", "Password does not meet the policy"
        ) from None

    try:
        user = register_user(
            session,
            str(payload.email),
            payload.password,
            payload.role,
            demo_mode=settings.demo_mode,
        )
    except DuplicateEmailError:
        raise api_error(409, "EMAIL_ALREADY_EXISTS", "Email is already registered") from None
    except RegistrationPersistenceError:
        raise api_error(500, "INTERNAL_ERROR", "Unable to register user") from None

    if user.status == "active":
        return TokenResponse(access_token=create_access_token(user.id))
    return VerificationRequiredResponse()


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    session: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    user = authenticate_user(session, str(payload.email), payload.password)
    if user is None:
        raise api_error(401, "INVALID_CREDENTIALS", "Invalid credentials")
    return TokenResponse(access_token=create_access_token(user.id))
