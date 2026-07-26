from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.errors import api_error
from app.db.session import get_db
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def readiness(session: Annotated[Session, Depends(get_db)]) -> HealthResponse:
    try:
        session.execute(text("SELECT 1"))
    except Exception:
        raise api_error(503, "SERVICE_UNAVAILABLE", "Service unavailable") from None
    return HealthResponse(status="ok", database="ready")
