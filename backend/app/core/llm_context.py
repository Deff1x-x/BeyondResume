"""Per-request LLM provider resolution for Demo Mode acceleration."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator, Literal, cast

from app.core.config import settings

LlmProviderName = Literal["mock", "openai"]

_force_mock: ContextVar[bool] = ContextVar("force_mock_llm", default=False)


def set_force_mock_llm(enabled: bool) -> None:
    _force_mock.set(enabled)


def resolve_llm_provider() -> LlmProviderName:
    """Return mock for demo sessions; otherwise the process setting."""
    if _force_mock.get():
        return "mock"
    provider = (settings.llm_provider or "mock").lower()
    # Provider factories remain responsible for rejecting unsupported values.
    # The cast preserves that validation path while keeping the resolver typed.
    return cast(LlmProviderName, provider)


@contextmanager
def force_mock_llm(enabled: bool = True) -> Iterator[None]:
    token = _force_mock.set(enabled)
    try:
        yield
    finally:
        _force_mock.reset(token)
