"""Official OpenAI SDK transport for AI Hiring Intelligence."""

from __future__ import annotations

import logging
from time import monotonic

from app.core.config import settings
from app.schemas.ai_hiring_intelligence import AiHiringIntelligenceResponse

logger = logging.getLogger(__name__)


class OpenAIHiringIntelligenceProviderError(Exception):
    """The provider could not return a JSON response."""


class OpenAIHiringIntelligenceProvider:
    """Thin provider transport; schema and semantic validation stay in the service."""

    provider_name = "openai"

    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise OpenAIHiringIntelligenceProviderError("OpenAI API key is not configured")
        try:
            from openai import OpenAI
        except ImportError as error:
            raise OpenAIHiringIntelligenceProviderError("OpenAI SDK is not installed") from error
        self._client = OpenAI(api_key=settings.openai_api_key, timeout=settings.llm_timeout_seconds)
        self.model = settings.openai_model

    def generate(self, prompt: str) -> str:
        started = monotonic()
        try:
            response = self._client.beta.chat.completions.parse(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format=AiHiringIntelligenceResponse,
            )
            message = response.choices[0].message
            if getattr(message, "refusal", None):
                raise OpenAIHiringIntelligenceProviderError("OpenAI response was refused")
            parsed = getattr(message, "parsed", None)
            if parsed is None:
                raise OpenAIHiringIntelligenceProviderError("OpenAI response was empty")
            content = parsed.model_dump_json()
        except Exception as error:
            logger.warning(
                "AI Hiring Intelligence provider failed",
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
            raise OpenAIHiringIntelligenceProviderError(
                f"OpenAI request failed ({type(error).__name__})"
            ) from error
        logger.info(
            "AI Hiring Intelligence provider completed",
            extra={"provider": self.provider_name, "model": self.model, "latency_ms": round((monotonic() - started) * 1000), "success": True},
        )
        return content


def _safe_error_message(error: Exception) -> str:
    """Do not allow an SDK error payload to become an application log payload."""
    if isinstance(error, OpenAIHiringIntelligenceProviderError):
        return str(error)
    return "OpenAI SDK request failed"
