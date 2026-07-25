"""Official OpenAI SDK transport for AI Interview Questions."""

from __future__ import annotations

import logging
from time import monotonic

from app.core.config import settings
from app.schemas.interview_questions import InterviewQuestionsResponse

logger = logging.getLogger(__name__)


class OpenAIInterviewQuestionsProviderError(Exception):
    """The provider could not return a JSON response."""


class OpenAIInterviewQuestionsProvider:
    """Thin provider transport; schema and safety validation stay in the service."""

    provider_name = "openai"

    def __init__(self) -> None:
        if not settings.llm_api_key:
            raise OpenAIInterviewQuestionsProviderError("OpenAI API key is not configured")
        try:
            from openai import OpenAI
        except ImportError as error:
            raise OpenAIInterviewQuestionsProviderError("OpenAI SDK is not installed") from error
        self._client = OpenAI(api_key=settings.llm_api_key, timeout=settings.llm_timeout_seconds)
        self.model = settings.llm_model

    def generate(self, prompt: str) -> str:
        started = monotonic()
        try:
            response = self._client.beta.chat.completions.parse(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format=InterviewQuestionsResponse,
            )
            message = response.choices[0].message
            if getattr(message, "refusal", None):
                raise OpenAIInterviewQuestionsProviderError("OpenAI response was refused")
            parsed = getattr(message, "parsed", None)
            if parsed is None:
                raise OpenAIInterviewQuestionsProviderError("OpenAI response was empty")
            content = str(parsed.model_dump_json())
        except Exception as error:
            logger.warning(
                "AI Interview Questions provider failed",
                extra={
                    "provider": self.provider_name,
                    "model": self.model,
                    "latency_ms": round((monotonic() - started) * 1000),
                    "success": False,
                    "failure_stage": "during_openai_request",
                    "exception_type": type(error).__name__,
                    "exception_message": _safe_error_message(error),
                    "http_status": getattr(error, "status_code", None),
                    "openai_error_code": getattr(error, "code", None),
                },
            )
            raise OpenAIInterviewQuestionsProviderError(
                f"OpenAI request failed ({type(error).__name__})"
            ) from error
        logger.info(
            "AI Interview Questions provider completed",
            extra={
                "provider": self.provider_name,
                "model": self.model,
                "latency_ms": round((monotonic() - started) * 1000),
                "success": True,
            },
        )
        return content


def _safe_error_message(error: Exception) -> str:
    if isinstance(error, OpenAIInterviewQuestionsProviderError):
        return str(error)
    return "OpenAI SDK request failed"
