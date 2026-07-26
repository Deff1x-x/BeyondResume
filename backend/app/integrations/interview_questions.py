"""Provider boundary for AI Interview Questions."""

from __future__ import annotations

from typing import Protocol

from app.core.config import settings


class InterviewQuestionsProvider(Protocol):
    """Transport contract consumed by the domain service."""

    def generate(self, prompt: str) -> str: ...


class InterviewQuestionsProviderConfigurationError(Exception):
    """The configured provider is not supported."""


def get_interview_questions_provider() -> InterviewQuestionsProvider:
    """Wire the configured transport while keeping implementations lazy."""
    if settings.llm_provider == "mock":
        from app.integrations.mock_interview_questions import MockInterviewQuestionsProvider

        return MockInterviewQuestionsProvider()
    if settings.llm_provider == "openai":
        from app.integrations.openai_interview_questions import OpenAIInterviewQuestionsProvider

        return OpenAIInterviewQuestionsProvider()

    raise InterviewQuestionsProviderConfigurationError(
        f"Unsupported AI Interview Questions provider: {settings.llm_provider!r}"
    )
