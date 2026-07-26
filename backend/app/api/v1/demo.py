from typing import Annotated, Literal

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user
from app.api.errors import api_error
from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.services.demo_seed import get_demo_user_for_role, reset_demo_tenants
from app.services.demo_users import is_demo_user

router = APIRouter(prefix="/demo", tags=["demo"])


class DemoStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool
    roles: list[Literal["candidate", "employer"]] = Field(
        default_factory=lambda: ["candidate", "employer"]
    )


class DemoStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["candidate", "employer"]


class DemoResetResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool = True
    role: Literal["candidate", "employer"]
    access_token: str
    token_type: Literal["bearer"] = "bearer"


def _require_demo_mode() -> None:
    if not settings.demo_mode:
        raise api_error(404, "DEMO_DISABLED", "Demo Mode is not enabled")


@router.get("/status", response_model=DemoStatusResponse)
def demo_status() -> DemoStatusResponse:
    return DemoStatusResponse(enabled=bool(settings.demo_mode))


@router.post("/start", response_model=TokenResponse)
def demo_start(
    payload: DemoStartRequest,
    session: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    _require_demo_mode()
    try:
        user = get_demo_user_for_role(session, payload.role)
        access_token = create_access_token(user.id, demo=True)
    except Exception:
        raise api_error(500, "DEMO_SEED_FAILED", "Unable to prepare the demo workspace") from None
    return TokenResponse(access_token=access_token)


@router.post("/reset", response_model=DemoResetResponse)
def demo_reset(
    session: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> DemoResetResponse:
    _require_demo_mode()
    if not is_demo_user(current_user):
        raise api_error(403, "FORBIDDEN", "Only demo sessions can restart the demo")

    role: Literal["candidate", "employer"] = (
        "employer" if current_user.role == "employer" else "candidate"
    )
    try:
        reset_demo_tenants(session)
        user = get_demo_user_for_role(session, role)
        access_token = create_access_token(user.id, demo=True)
    except Exception:
        raise api_error(500, "DEMO_RESET_FAILED", "Unable to reset the demo workspace") from None

    return DemoResetResponse(role=role, access_token=access_token)
