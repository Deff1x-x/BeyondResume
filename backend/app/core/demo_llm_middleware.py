"""ASGI middleware that forces mock LLM for Demo Mode JWT sessions.

Sync FastAPI dependencies and endpoints run in separate threadpool workers, so a
ContextVar set inside ``get_current_active_user`` is not visible to the route body.
Setting the flag in async middleware propagates into both workers via AnyIO.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.llm_context import set_force_mock_llm
from app.core.security import access_token_is_demo


class DemoLlmMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        token = _bearer_token(request)
        set_force_mock_llm(bool(token and access_token_is_demo(token)))
        try:
            return await call_next(request)
        finally:
            set_force_mock_llm(False)


def _bearer_token(request: Request) -> str | None:
    header = request.headers.get("Authorization")
    if not header:
        return None
    scheme, _, value = header.partition(" ")
    if scheme.lower() != "bearer" or not value.strip():
        return None
    return value.strip()
