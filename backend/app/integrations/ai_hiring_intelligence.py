"""Provider boundary for AI Hiring Intelligence."""

from __future__ import annotations

from typing import Protocol

from app.core.config import settings
from app.core.llm_context import resolve_llm_provider


class HiringIntelligenceProvider(Protocol):
    """Transport contract consumed by the domain service."""

    def generate(self, prompt: str) -> str: ...


class HiringIntelligenceProviderConfigurationError(Exception):
    """The configured provider is not supported."""


def get_hiring_intelligence_provider() -> HiringIntelligenceProvider:
    """Wire the configured transport while keeping implementations lazy."""
    _ = settings  # Public module compatibility for provider configuration tests.
    provider = resolve_llm_provider()
    if provider == "mock":
        from app.integrations.mock_hiring_intelligence import MockHiringIntelligenceProvider

        return MockHiringIntelligenceProvider()
    if provider == "openai":
        from app.integrations.openai_hiring_intelligence import OpenAIHiringIntelligenceProvider

        return OpenAIHiringIntelligenceProvider()

    raise HiringIntelligenceProviderConfigurationError(
        f"Unsupported AI Hiring Intelligence provider: {provider!r}"
    )
