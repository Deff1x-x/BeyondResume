from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.auth import PublicUserResponse

router = APIRouter(tags=["users"])


@router.get("/me", response_model=PublicUserResponse)
def get_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> PublicUserResponse:
    return PublicUserResponse.model_validate(current_user)
