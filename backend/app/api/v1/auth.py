from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.errors import api_error
from app.core.security import create_access_token
from app.db.session import get_db
from app.schemas.auth import LoginRequest, PublicUserResponse, RegisterRequest, TokenResponse
from app.services.auth import DuplicateEmailError, authenticate_user, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=PublicUserResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    session: Annotated[Session, Depends(get_db)],
) -> PublicUserResponse:
    try:
        user = register_user(session, str(payload.email), payload.password, payload.role)
    except DuplicateEmailError:
        raise api_error(409, "DUPLICATE_EMAIL", "Email is already registered") from None
    return PublicUserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    session: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    user = authenticate_user(session, str(payload.email), payload.password)
    if user is None:
        raise api_error(401, "INVALID_CREDENTIALS", "Invalid credentials")
    return TokenResponse(access_token=create_access_token(user.id))
