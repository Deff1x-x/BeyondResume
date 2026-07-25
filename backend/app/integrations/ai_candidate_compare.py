"""Provider boundary for AI Candidate Compare."""

from __future__ import annotations

from typing import Protocol

from app.core.config import settings


class AiCandidateCompareProvider(Protocol):
    """Transport contract consumed by the domain service."""

    def generate(self, prompt: str) -> str: ...


class AiCandidateCompareProviderConfigurationError(Exception):
    """The configured provider is not supported."""


def get_ai_candidate_compare_provider() -> AiCandidateCompareProvider:
    """Wire the configured transport while keeping implementations lazy."""
    if settings.llm_provider == "mock":
        from app.integrations.mock_ai_candidate_compare import MockAiCandidateCompareProvider

        return MockAiCandidateCompareProvider()
    if settings.llm_provider == "openai":
        from app.integrations.openai_ai_candidate_compare import OpenAIAiCandidateCompareProvider

        return OpenAIAiCandidateCompareProvider()

    raise AiCandidateCompareProviderConfigurationError(
        f"Unsupported AI Candidate Compare provider: {settings.llm_provider!r}"
    )


def generation_mode_for_provider() -> str:
    """Backend-owned live/mock flag derived from settings, never from model output."""
    if settings.llm_provider == "openai":
        return "live"
    return "mock"
