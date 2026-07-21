"""Provider boundary for AI Hiring Intelligence."""

from __future__ import annotations

from typing import Protocol


class HiringIntelligenceProvider(Protocol):
    """Transport contract consumed by the domain service."""

    def generate(self, prompt: str) -> str: ...


def get_hiring_intelligence_provider() -> HiringIntelligenceProvider:
    """Wire the configured transport without coupling the service to OpenAI."""
    from app.integrations.openai_hiring_intelligence import OpenAIHiringIntelligenceProvider

    return OpenAIHiringIntelligenceProvider()
