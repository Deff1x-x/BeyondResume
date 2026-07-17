from collections.abc import Sequence
from uuid import uuid4

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.requests import Request
from fastapi.responses import JSONResponse


def api_error(
    status_code: int,
    code: str,
    message: str,
    details: Sequence[dict[str, str]] | None = None,
    headers: dict[str, str] | None = None,
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message, "details": list(details or [])},
        headers=headers,
    )


async def http_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, HTTPException):
        raise exc

    detail: dict[str, object] = exc.detail if isinstance(exc.detail, dict) else {}
    error = {
        "code": str(detail.get("code", "HTTP_ERROR")),
        "message": str(detail.get("message", "Request failed")),
        "details": detail.get("details", []),
        "request_id": str(uuid4()),
    }
    return JSONResponse(status_code=exc.status_code, content={"error": error}, headers=exc.headers)


async def validation_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        raise exc

    details = [
        {"field": ".".join(str(part) for part in error["loc"]), "issue": error["type"]}
        for error in exc.errors()
    ]
    error = {
        "code": "VALIDATION_ERROR",
        "message": "Validation error",
        "details": details,
        "request_id": str(uuid4()),
    }
    return JSONResponse(status_code=422, content=jsonable_encoder({"error": error}))
