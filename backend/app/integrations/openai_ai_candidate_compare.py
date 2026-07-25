"""Official OpenAI SDK transport for AI Candidate Compare."""

from __future__ import annotations

import logging
from time import monotonic
from typing import Any

from app.core.config import settings
from app.schemas.ai_candidate_compare import AiCandidateCompareLlmPayload

logger = logging.getLogger(__name__)

# Cold structured-output latency on gpt-5-mini is dominated by reasoning tokens,
# not prompt size. "minimal" reasoning keeps grounded, semantically valid
# comparisons while roughly halving cold latency versus the model default.
REASONING_EFFORT = "minimal"


class OpenAIAiCandidateCompareProviderError(Exception):
    """The provider could not return a JSON response."""


class OpenAIAiCandidateCompareProvider:
    """Thin provider transport; schema and semantic validation stay in the service."""

    provider_name = "openai"

    def __init__(self, client: Any | None = None) -> None:
        if not settings.llm_api_key:
            raise OpenAIAiCandidateCompareProviderError("OpenAI API key is not configured")
        if client is not None:
            self._client = client
        else:
            try:
                from openai import OpenAI
            except ImportError as error:
                raise OpenAIAiCandidateCompareProviderError(
                    "OpenAI SDK is not installed"
                ) from error
            self._client = OpenAI(
                api_key=settings.llm_api_key, timeout=settings.llm_timeout_seconds
            )
        self.model = settings.llm_model

    def generate(self, prompt: str) -> str:
        started = monotonic()
        try:
            response = self._client.beta.chat.completions.parse(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format=AiCandidateCompareLlmPayload,
                reasoning_effort=REASONING_EFFORT,
            )
            message = response.choices[0].message
            if getattr(message, "refusal", None):
                raise OpenAIAiCandidateCompareProviderError("OpenAI response was refused")
            parsed = getattr(message, "parsed", None)
            if parsed is None:
                raise OpenAIAiCandidateCompareProviderError("OpenAI response was empty")
            content = str(parsed.model_dump_json())
        except Exception as error:
            logger.warning(
                "AI Candidate Compare provider failed",
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
            raise OpenAIAiCandidateCompareProviderError(
                f"OpenAI request failed ({type(error).__name__})"
            ) from error
        logger.info(
            "AI Candidate Compare provider completed",
            extra={
                "provider": self.provider_name,
                "model": self.model,
                "latency_ms": round((monotonic() - started) * 1000),
                "success": True,
            },
        )
        return content


def _safe_error_message(error: Exception) -> str:
    """Do not allow an SDK error payload to become an application log payload."""
    if isinstance(error, OpenAIAiCandidateCompareProviderError):
        return str(error)
    return "OpenAI SDK request failed"
