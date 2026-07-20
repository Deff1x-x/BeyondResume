"""LLM explanation layer for already-computed deterministic match details."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from hashlib import sha256
import json
from threading import Lock
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import ValidationError

from app.core.config import settings
from app.schemas.employer import AiMatchExplanationResponse, MatchDetailsResponse

_CACHE_LIMIT = 128


class MatchExplanationUnavailableError(Exception):
    """The LLM could not supply a safe structured explanation."""


class LlmProvider(Protocol):
    def generate(self, prompt: str) -> str: ...


@dataclass(frozen=True, slots=True)
class MatchExplanationInput:
    confirmed_skills: tuple[str, ...]
    evidence_sources: tuple[str, ...]
    vacancy_title: str
    required_skills: tuple[str, ...]
    preferred_skills: tuple[str, ...]
    score: int
    matched_required: tuple[str, ...]
    matched_preferred: tuple[str, ...]
    missing_required: tuple[str, ...]
    missing_preferred: tuple[str, ...]
    roadmap_items: tuple[tuple[str, tuple[str, ...]], ...]

    def as_payload(self) -> dict[str, object]:
        return {
            "candidate": {
                "confirmed_skills": list(self.confirmed_skills),
                "evidence_sources": list(self.evidence_sources),
            },
            "vacancy": {
                "title": self.vacancy_title,
                "required_skills": list(self.required_skills),
                "preferred_skills": list(self.preferred_skills),
            },
            "match": {
                "percentage": self.score,
                "matched_required": list(self.matched_required),
                "matched_preferred": list(self.matched_preferred),
                "missing_required": list(self.missing_required),
                "missing_preferred": list(self.missing_preferred),
            },
            "roadmap": [
                {"title": title, "missing_skills": list(skills)}
                for title, skills in self.roadmap_items
            ],
        }

    def cache_payload(self) -> dict[str, object]:
        """Only match/roadmap state controls reuse; profile changes alone do not regenerate."""
        payload = self.as_payload()
        return {
            "vacancy": payload["vacancy"],
            "match": payload["match"],
            "roadmap": payload["roadmap"],
        }


class _ExplanationCache:
    def __init__(self) -> None:
        self._items: OrderedDict[str, AiMatchExplanationResponse] = OrderedDict()
        self._lock = Lock()

    def get(self, key: str) -> AiMatchExplanationResponse | None:
        with self._lock:
            value = self._items.get(key)
            if value is not None:
                self._items.move_to_end(key)
            return value

    def put(self, key: str, value: AiMatchExplanationResponse) -> None:
        with self._lock:
            self._items[key] = value
            self._items.move_to_end(key)
            while len(self._items) > _CACHE_LIMIT:
                self._items.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()


_cache = _ExplanationCache()


def build_explanation_input(
    *,
    details: MatchDetailsResponse,
    confirmed_skills: list[str],
    vacancy_title: str,
    required_skills: list[str],
    preferred_skills: list[str],
) -> MatchExplanationInput:
    """Create the allow-listed LLM input; raw resume/GitHub payloads never enter it."""
    return MatchExplanationInput(
        confirmed_skills=tuple(confirmed_skills),
        evidence_sources=tuple(sorted({item.source_type for item in details.evidence})),
        vacancy_title=vacancy_title,
        required_skills=tuple(required_skills),
        preferred_skills=tuple(preferred_skills),
        score=details.match.score,
        matched_required=tuple(details.match.required.matched),
        matched_preferred=tuple(details.match.preferred.matched),
        missing_required=tuple(details.match.required.missing),
        missing_preferred=tuple(details.match.preferred.missing),
        roadmap_items=tuple(
            (item.title, tuple(item.missing_skills)) for item in details.roadmap
        ),
    )


def build_explanation_prompt(explanation_input: MatchExplanationInput) -> str:
    payload = json.dumps(explanation_input.as_payload(), ensure_ascii=False, sort_keys=True)
    return (
        "Explain only the supplied deterministic candidate-vacancy match. Return a valid JSON "
        "object with exactly summary, strengths, gaps, and next_steps; every value except "
        "summary must be an array of concise strings. Do not return Markdown. Do not calculate "
        "a new score, infer skills, invent facts, or use information not in the input. Explain "
        "why the given score resulted, confirmed strengths, fulfilled and missing requirements, "
        "and how the supplied roadmap addresses gaps. Keep the total response roughly 150-250 words.\n"
        f"INPUT:\n{payload}"
    )


def explain_match(explanation_input: MatchExplanationInput) -> AiMatchExplanationResponse:
    key = sha256(
        json.dumps(explanation_input.cache_payload(), ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    cached = _cache.get(key)
    if cached is not None:
        return cached
    try:
        response = parse_explanation_json(get_llm_provider().generate(build_explanation_prompt(explanation_input)))
    except (MatchExplanationUnavailableError, ValidationError, ValueError) as error:
        raise MatchExplanationUnavailableError from error
    _cache.put(key, response)
    return response


def parse_explanation_json(content: str) -> AiMatchExplanationResponse:
    try:
        payload = json.loads(content)
    except (TypeError, json.JSONDecodeError) as error:
        raise MatchExplanationUnavailableError("LLM response was not valid JSON") from error
    try:
        return AiMatchExplanationResponse.model_validate(payload)
    except ValidationError as error:
        raise MatchExplanationUnavailableError("LLM response did not match the explanation schema") from error


def get_llm_provider() -> LlmProvider:
    if settings.llm_provider == "mock":
        return _MockLlmProvider()
    if settings.llm_provider == "openai":
        return _OpenAiLlmProvider()
    raise MatchExplanationUnavailableError("LLM provider is not configured")


class _MockLlmProvider:
    """Local development provider; production uses the configured OpenAI provider."""

    def generate(self, prompt: str) -> str:
        payload = json.loads(prompt.partition("INPUT:\n")[2])
        match = payload["match"]
        candidate = payload["candidate"]
        roadmap = payload["roadmap"]
        missing = [*match["missing_required"], *match["missing_preferred"]]
        strengths = [
            f"Confirmed {skill} experience directly supports a listed requirement for this vacancy."
            for skill in match["matched_required"][:2]
        ]
        gaps = [
            f"{skill} is a listed requirement that is not yet confirmed, so it lowers the current deterministic match."
            for skill in missing[:3]
        ]
        next_steps = [
            f"Complete the roadmap item {item['title']} to address {', '.join(item['missing_skills'])} in the existing gap analysis."
            for item in roadmap[:3]
        ]
        summary = (
            f"The current deterministic match is {match['percentage']}%. It is based only on "
            f"the supplied required and preferred vacancy skills compared with the confirmed "
            f"candidate skills supported by {', '.join(candidate['evidence_sources']) or 'available evidence'} "
            f"sources. This explanation does not infer additional skills or change the score. "
            f"It highlights the requirements already matched, the listed gaps, and the existing roadmap "
            f"items that can address those gaps."
        )
        return json.dumps({"summary": summary, "strengths": strengths, "gaps": gaps, "next_steps": next_steps})


class _OpenAiLlmProvider:
    def generate(self, prompt: str) -> str:
        if not settings.llm_api_key:
            raise MatchExplanationUnavailableError("LLM API key is not configured")
        request_body = json.dumps(
            {
                "model": settings.llm_model,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
            }
        ).encode("utf-8")
        request = Request(
            "https://api.openai.com/v1/chat/completions",
            data=request_body,
            headers={
                "Authorization": f"Bearer {settings.llm_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=settings.llm_timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"]
        except (HTTPError, URLError, KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
            raise MatchExplanationUnavailableError("LLM request failed") from error
