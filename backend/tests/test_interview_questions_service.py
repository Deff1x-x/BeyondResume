"""Prompt, mock, cache, and dependency tests for AI Interview Questions."""

from __future__ import annotations

import json
from uuid import uuid4

import pytest

from app.integrations.mock_interview_questions import MockInterviewQuestionsProvider
from app.prompts import interview_questions as prompt_module
from app.prompts.interview_questions import PROMPT_VERSION, SCHEMA_VERSION, SYSTEM_RULES
from app.services import interview_questions as service_module
from app.services.interview_questions import (
    InterviewQuestionsContext,
    InterviewQuestionsUnavailableError,
    build_interview_questions_prompt,
    clear_interview_questions_cache,
    get_interview_questions,
    parse_interview_questions_response,
)


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    clear_interview_questions_cache()


def _safe_question_payload(
    *, question: str, reason: str = "Job-relevant probe."
) -> dict[str, object]:
    return {
        "category": "technical",
        "question": question,
        "reason": reason,
        "target_skill": "Python",
        "evidence_basis": "Sources: github_repository",
    }


def _context(
    *,
    missing_required: list[str] | None = None,
    matched_required: list[dict[str, object]] | None = None,
) -> InterviewQuestionsContext:
    return InterviewQuestionsContext(
        vacancy_id=str(uuid4()),
        candidate_id=str(uuid4()),
        facts={
            "vacancy_title": "Backend Engineer",
            "vacancy_description": "Build APIs",
            "required_skills": ["Python", "Redis"],
            "preferred_skills": ["PostgreSQL"],
            "match_percentage": 72,
            "candidate_headline": "Backend Engineer",
            "matched_required_skills": matched_required
            or [
                {
                    "name": "Python",
                    "evidence_title": "payments-api",
                    "evidence_basis": "Sources: github_repository",
                    "confidence": 88,
                }
            ],
            "matched_preferred_skills": [],
            "passport_skills": [
                {
                    "name": "Python",
                    "confidence": 88,
                    "evidence_count": 2,
                    "source_types": ["github_repository"],
                }
            ],
            "evidence_summaries": [{"title": "payments-api", "source_type": "github_repository"}],
        },
        gaps={
            "missing_required_skills": missing_required or ["Redis"],
            "missing_preferred_skills": [],
            "low_confidence_required_skills": [],
        },
    )


def test_prompt_contains_required_rules() -> None:
    assert PROMPT_VERSION == "interview-questions-v1"
    assert SCHEMA_VERSION == "interview-questions-schema-v1"
    for fragment in (
        "FACTS",
        "GAPS",
        "1 to 8",
        "filler",
        "hiring verdict",
        "invent",
        "protected trait",
        "observable work behavior",
        "technical",
        "experience",
        "risk_validation",
        "ownership",
    ):
        assert fragment in SYSTEM_RULES
    assert "exactly 8" not in SYSTEM_RULES.casefold()
    prompt = build_interview_questions_prompt(_context())
    assert "INPUT:" in prompt
    assert "Backend Engineer" in prompt


def test_prompt_module_does_not_import_ai_hiring() -> None:
    source = prompt_module.__file__
    assert source is not None
    text = open(source, encoding="utf-8").read()
    assert "ai_hiring" not in text
    assert "HiringIntelligence" not in text


def test_service_module_does_not_import_ai_hiring() -> None:
    source = service_module.__file__
    assert source is not None
    text = open(source, encoding="utf-8").read()
    assert "ai_hiring_intelligence" not in text
    assert "get_hiring_intelligence" not in text


def test_mock_is_deterministic_and_covers_gaps_and_evidence() -> None:
    provider = MockInterviewQuestionsProvider()
    prompt = build_interview_questions_prompt(_context())
    first = provider.generate(prompt)
    second = provider.generate(prompt)
    assert first == second
    response = parse_interview_questions_response(first)
    categories = {item.category for item in response.questions}
    assert "risk_validation" in categories
    assert "technical" in categories or "experience" in categories
    assert any(item.target_skill == "Redis" for item in response.questions)
    assert any(
        item.evidence_basis and "payments-api" in item.evidence_basis for item in response.questions
    )


def test_mock_sparse_context_is_safe() -> None:
    context = InterviewQuestionsContext(
        vacancy_id=str(uuid4()),
        candidate_id=str(uuid4()),
        facts={
            "vacancy_title": "Generalist",
            "vacancy_description": None,
            "required_skills": [],
            "preferred_skills": [],
            "match_percentage": 0,
            "candidate_headline": None,
            "matched_required_skills": [],
            "matched_preferred_skills": [],
            "passport_skills": [],
            "evidence_summaries": [],
        },
        gaps={
            "missing_required_skills": [],
            "missing_preferred_skills": [],
            "low_confidence_required_skills": [],
        },
    )
    response = parse_interview_questions_response(
        MockInterviewQuestionsProvider().generate(build_interview_questions_prompt(context))
    )
    assert 1 <= len(response.questions) <= 2
    assert all("pregnant" not in item.question.casefold() for item in response.questions)
    assert all(
        "are you a responsible" not in item.question.casefold() for item in response.questions
    )


def test_cache_hit_skips_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    context = _context()
    calls = {"count": 0}

    class _CountingProvider:
        def generate(self, prompt: str) -> str:
            calls["count"] += 1
            return json.dumps(
                {"questions": [_safe_question_payload(question="How have you used Python?")]}
            )

    monkeypatch.setattr(
        service_module, "get_interview_questions_provider", lambda: _CountingProvider()
    )
    first = get_interview_questions(context, refresh=False)
    second = get_interview_questions(context, refresh=False)
    assert first.model_dump() == second.model_dump()
    assert calls["count"] == 1


def test_successful_refresh_replaces_cache_entry(monkeypatch: pytest.MonkeyPatch) -> None:
    context = _context()
    calls = {"count": 0}

    class _SequenceProvider:
        def generate(self, prompt: str) -> str:
            calls["count"] += 1
            question = (
                "How have you used Python in APIs?"
                if calls["count"] == 1
                else "How have you used Redis caching?"
            )
            return json.dumps({"questions": [_safe_question_payload(question=question)]})

    monkeypatch.setattr(
        service_module, "get_interview_questions_provider", lambda: _SequenceProvider()
    )
    first = get_interview_questions(context, refresh=False)
    assert first.questions[0].question == "How have you used Python in APIs?"
    refreshed = get_interview_questions(context, refresh=True)
    assert refreshed.questions[0].question == "How have you used Redis caching?"
    assert calls["count"] == 2
    cached = get_interview_questions(context, refresh=False)
    assert cached.questions[0].question == "How have you used Redis caching?"
    assert calls["count"] == 2


def test_failed_refresh_preserves_previous_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    context = _context()
    calls = {"count": 0}

    class _FlakyProvider:
        def generate(self, prompt: str) -> str:
            calls["count"] += 1
            if calls["count"] == 1:
                return json.dumps(
                    {
                        "questions": [
                            _safe_question_payload(question="How have you used Python in APIs?")
                        ]
                    }
                )
            raise RuntimeError("provider down")

    monkeypatch.setattr(
        service_module, "get_interview_questions_provider", lambda: _FlakyProvider()
    )
    cached = get_interview_questions(context, refresh=False)
    with pytest.raises(InterviewQuestionsUnavailableError):
        get_interview_questions(context, refresh=True)
    assert calls["count"] == 2
    again = get_interview_questions(context, refresh=False)
    assert again.model_dump() == cached.model_dump()
    assert again.questions[0].question == "How have you used Python in APIs?"
    assert calls["count"] == 2


def test_unsafe_response_is_not_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    context = _context()
    calls = {"count": 0}

    class _UnsafeThenSafeProvider:
        def generate(self, prompt: str) -> str:
            calls["count"] += 1
            if calls["count"] == 1:
                return json.dumps(
                    {
                        "questions": [
                            _safe_question_payload(
                                question="How old are you and how does that affect your plans?"
                            )
                        ]
                    }
                )
            return json.dumps(
                {"questions": [_safe_question_payload(question="How have you used Python?")]}
            )

    monkeypatch.setattr(
        service_module, "get_interview_questions_provider", lambda: _UnsafeThenSafeProvider()
    )
    with pytest.raises(InterviewQuestionsUnavailableError):
        get_interview_questions(context, refresh=False)
    safe = get_interview_questions(context, refresh=False)
    assert safe.questions[0].question == "How have you used Python?"
    assert calls["count"] == 2


def test_duplicate_response_is_not_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    context = _context()
    calls = {"count": 0}

    class _DuplicateThenSafeProvider:
        def generate(self, prompt: str) -> str:
            calls["count"] += 1
            if calls["count"] == 1:
                return json.dumps(
                    {
                        "questions": [
                            _safe_question_payload(question="How have you used Python?"),
                            _safe_question_payload(question="how have you used python?"),
                        ]
                    }
                )
            return json.dumps(
                {"questions": [_safe_question_payload(question="How have you used Redis?")]}
            )

    monkeypatch.setattr(
        service_module, "get_interview_questions_provider", lambda: _DuplicateThenSafeProvider()
    )
    with pytest.raises(InterviewQuestionsUnavailableError):
        get_interview_questions(context, refresh=False)
    safe = get_interview_questions(context, refresh=False)
    assert safe.questions[0].question == "How have you used Redis?"
    assert calls["count"] == 2


def test_requirement_change_invalidates_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"count": 0}

    class _CountingProvider:
        def generate(self, prompt: str) -> str:
            calls["count"] += 1
            return json.dumps(
                {"questions": [_safe_question_payload(question=f"Probe number {calls['count']}")]}
            )

    monkeypatch.setattr(
        service_module, "get_interview_questions_provider", lambda: _CountingProvider()
    )
    first_context = _context(missing_required=["Redis"])
    second_context = _context(missing_required=["Kafka"])
    get_interview_questions(first_context, refresh=False)
    get_interview_questions(second_context, refresh=False)
    assert calls["count"] == 2


def test_invalid_json_rejected() -> None:
    with pytest.raises(InterviewQuestionsUnavailableError):
        parse_interview_questions_response("not-json")


def test_cache_write_happens_only_after_full_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context()
    events: list[str] = []

    class _TrackedProvider:
        def generate(self, prompt: str) -> str:
            events.append("generate")
            return json.dumps(
                {"questions": [_safe_question_payload(question="How have you used Python?")]}
            )

    original_parse = service_module.parse_interview_questions_response
    original_put = service_module._cache.put

    def tracked_parse(content: str):
        events.append("parse")
        result = original_parse(content)
        events.append("validated")
        return result

    def tracked_put(key: str, value: object) -> None:
        events.append("cache_write")
        original_put(key, value)

    monkeypatch.setattr(
        service_module, "get_interview_questions_provider", lambda: _TrackedProvider()
    )
    monkeypatch.setattr(service_module, "parse_interview_questions_response", tracked_parse)
    monkeypatch.setattr(service_module._cache, "put", tracked_put)

    get_interview_questions(context, refresh=False)
    assert events == ["generate", "parse", "validated", "cache_write"]
