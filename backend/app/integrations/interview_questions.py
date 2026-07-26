"""Provider boundary for AI Interview Questions."""

from __future__ import annotations

from typing import Protocol

from app.core.llm_context import resolve_llm_provider


class InterviewQuestionsProvider(Protocol):
    """Transport contract consumed by the domain service."""

    def generate(self, prompt: str) -> str: ...


class InterviewQuestionsProviderConfigurationError(Exception):
    """The configured provider is not supported."""


def get_interview_questions_provider() -> InterviewQuestionsProvider:
    """Wire the configured transport while keeping implementations lazy."""
    provider = resolve_llm_provider()
    if provider == "mock":
        from app.integrations.mock_interview_questions import MockInterviewQuestionsProvider

        return MockInterviewQuestionsProvider()
    if provider == "openai":
        from app.integrations.openai_interview_questions import OpenAIInterviewQuestionsProvider

        return OpenAIInterviewQuestionsProvider()

    raise InterviewQuestionsProviderConfigurationError(
        f"Unsupported AI Interview Questions provider: {provider!r}"
    )
