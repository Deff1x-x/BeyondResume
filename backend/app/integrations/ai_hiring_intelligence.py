"""Provider boundary for AI Hiring Intelligence."""

from __future__ import annotations

from typing import Protocol

from app.core.config import settings


class HiringIntelligenceProvider(Protocol):
    """Transport contract consumed by the domain service."""

    def generate(self, prompt: str) -> str: ...


class HiringIntelligenceProviderConfigurationError(Exception):
    """The configured provider is not supported."""


def get_hiring_intelligence_provider() -> HiringIntelligenceProvider:
    """Wire the configured transport while keeping implementations lazy."""
    if settings.llm_provider == "mock":
        from app.integrations.mock_hiring_intelligence import MockHiringIntelligenceProvider

        return MockHiringIntelligenceProvider()
    if settings.llm_provider == "openai":
        from app.integrations.openai_hiring_intelligence import OpenAIHiringIntelligenceProvider

        return OpenAIHiringIntelligenceProvider()

    raise HiringIntelligenceProviderConfigurationError(
        f"Unsupported AI Hiring Intelligence provider: {settings.llm_provider!r}"
    )
