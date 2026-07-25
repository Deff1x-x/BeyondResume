"""Unit tests for AI Candidate Compare service semantics and cache."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from app.schemas.ai_candidate_compare import AiCandidateCompareLlmPayload
from app.services import ai_candidate_compare as service


def _ids() -> tuple[UUID, UUID]:
    return (
        UUID("11111111-1111-1111-1111-111111111111"),
        UUID("22222222-2222-2222-2222-222222222222"),
    )


def _context(
    *,
    generation_mode: str = "mock",
) -> service.AiCandidateCompareContext:
    left, right = _ids()
    facts = {
        f"candidate:{left}:match-score": {"type": "match_score", "score": 80},
        f"candidate:{right}:match-score": {"type": "match_score", "score": 60},
        f"candidate:{left}:matched-required:python": {"type": "matched_required"},
        f"candidate:{right}:missing-required:python": {"type": "missing_required"},
        "vacancy:required-skill:python": {"type": "vacancy_required_skill"},
    }
    payload = {
        "candidates": [
            {
                "candidate_id": str(left),
                "candidate_label": "Candidate A",
                "match": {
                    "score": 80,
                    "required_matched": ["Python"],
                    "required_missing": [],
                    "preferred_matched": [],
                    "preferred_missing": [],
                },
            },
            {
                "candidate_id": str(right),
                "candidate_label": "Candidate B",
                "match": {
                    "score": 60,
                    "required_matched": [],
                    "required_missing": ["Python"],
                    "preferred_matched": [],
                    "preferred_missing": [],
                },
            },
        ],
        "facts": facts,
    }
    return service.AiCandidateCompareContext(
        vacancy_id=uuid4(),
        candidate_ids=(left, right),
        payload=payload,
        fact_ids=frozenset(facts),
        generation_mode=generation_mode,
    )


def _valid_payload() -> dict[str, object]:
    left, right = _ids()
    return {
        "summary": "Candidate A covers required Python better than Candidate B.",
        "candidate_assessments": [
            {
                "candidate_id": str(left),
                "strengths": [
                    {
                        "text": "Matches required Python.",
                        "fact_refs": [f"candidate:{left}:matched-required:python"],
                    }
                ],
                "risks": [
                    {
                        "text": "Score remains advisory only.",
                        "fact_refs": [f"candidate:{left}:match-score"],
                    }
                ],
            },
            {
                "candidate_id": str(right),
                "strengths": [
                    {
                        "text": "Has a system match score for comparison.",
                        "fact_refs": [f"candidate:{right}:match-score"],
                    }
                ],
                "risks": [
                    {
                        "text": "Missing required Python.",
                        "fact_refs": [
                            f"candidate:{right}:missing-required:python",
                            "vacancy:required-skill:python",
                        ],
                    }
                ],
            },
        ],
        "key_differences": [
            {
                "text": "Required Python coverage differs.",
                "fact_refs": [
                    f"candidate:{left}:matched-required:python",
                    f"candidate:{right}:missing-required:python",
                ],
            }
        ],
        "interview_focus_questions": [
            {
                "question": "How have you used Python in production services?",
                "candidate_ids": [str(left)],
                "fact_refs": [f"candidate:{left}:matched-required:python"],
            }
        ],
        "recommended_candidate_id": str(left),
        "recommendation_rationale": {
            "text": "Better required-skill coverage in supplied facts.",
            "fact_refs": [
                f"candidate:{left}:matched-required:python",
                f"candidate:{left}:match-score",
            ],
        },
        "confidence": "medium",
        "uncertainties": [
            {
                "text": "Evidence depth is limited to employer-safe summaries.",
                "fact_refs": [f"candidate:{left}:match-score"],
            }
        ],
    }


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    service.clear_ai_candidate_compare_cache()


def test_prompt_examples_validate_against_dto() -> None:
    from app.prompts import ai_candidate_compare as prompt_module

    AiCandidateCompareLlmPayload.model_validate_json(prompt_module.COMPLETE_EXAMPLE_JSON)
    AiCandidateCompareLlmPayload.model_validate_json(
        prompt_module.NO_RECOMMENDATION_EXAMPLE_JSON
    )


def test_successful_generation_uses_provider_and_sets_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    class FakeProvider:
        def generate(self, prompt: str) -> str:
            calls.append(prompt)
            return AiCandidateCompareLlmPayload.model_validate(_valid_payload()).model_dump_json()

    monkeypatch.setattr(service, "get_ai_candidate_compare_provider", lambda: FakeProvider())
    context = _context(generation_mode="live")
    result = service.get_ai_candidate_compare(context)

    assert len(calls) == 1
    assert "INPUT:" in calls[0]
    assert result.generation_mode == "live"
    assert result.candidate_ids == list(context.candidate_ids)
    assert result.recommended_candidate_id == context.candidate_ids[0]


def test_openai_path_cannot_succeed_without_provider_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        service,
        "get_ai_candidate_compare_provider",
        lambda: (_ for _ in ()).throw(RuntimeError("provider missing")),
    )
    with pytest.raises(service.AiCandidateCompareUnavailableError):
        service.get_ai_candidate_compare(_context(generation_mode="live"))


def test_provider_failure_is_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    class Boom:
        def generate(self, prompt: str) -> str:
            raise RuntimeError("provider down")

    monkeypatch.setattr(service, "get_ai_candidate_compare_provider", lambda: Boom())
    with pytest.raises(service.AiCandidateCompareUnavailableError):
        service.get_ai_candidate_compare(_context())


def test_parse_failure_is_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    class BadJson:
        def generate(self, prompt: str) -> str:
            return "not-json"

    monkeypatch.setattr(service, "get_ai_candidate_compare_provider", lambda: BadJson())
    with pytest.raises(service.AiCandidateCompareUnavailableError):
        service.get_ai_candidate_compare(_context())


def test_unknown_fact_ref_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _valid_payload()
    payload["candidate_assessments"][0]["strengths"][0]["fact_refs"] = ["vacancy:required-skill:nope"]

    class Provider:
        def generate(self, prompt: str) -> str:
            return AiCandidateCompareLlmPayload.model_validate(payload).model_dump_json()

    monkeypatch.setattr(service, "get_ai_candidate_compare_provider", lambda: Provider())
    with pytest.raises(service.AiCandidateCompareUnavailableError):
        service.get_ai_candidate_compare(_context())


def test_cross_candidate_fact_attribution_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    left, right = _ids()
    payload = _valid_payload()
    payload["candidate_assessments"][0]["strengths"][0]["fact_refs"] = [
        f"candidate:{right}:match-score"
    ]

    class Provider:
        def generate(self, prompt: str) -> str:
            return AiCandidateCompareLlmPayload.model_validate(payload).model_dump_json()

    monkeypatch.setattr(service, "get_ai_candidate_compare_provider", lambda: Provider())
    with pytest.raises(service.AiCandidateCompareUnavailableError):
        service.get_ai_candidate_compare(_context())


def test_unknown_candidate_id_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _valid_payload()
    payload["candidate_assessments"][0]["candidate_id"] = str(uuid4())

    class Provider:
        def generate(self, prompt: str) -> str:
            return AiCandidateCompareLlmPayload.model_validate(payload).model_dump_json()

    monkeypatch.setattr(service, "get_ai_candidate_compare_provider", lambda: Provider())
    with pytest.raises(service.AiCandidateCompareUnavailableError):
        service.get_ai_candidate_compare(_context())


def test_missing_assessment_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _valid_payload()
    payload["candidate_assessments"] = payload["candidate_assessments"][:1]

    class Provider:
        def generate(self, prompt: str) -> str:
            # Bypass DTO min_length by injecting after validate via raw JSON.
            return (
                '{"summary":"x","candidate_assessments":'
                + __import__("json").dumps(payload["candidate_assessments"])
                + ',"key_differences":[],"interview_focus_questions":[],'
                '"recommended_candidate_id":null,"recommendation_rationale":null,'
                '"confidence":"low","uncertainties":[]}'
            )

    monkeypatch.setattr(service, "get_ai_candidate_compare_provider", lambda: Provider())
    with pytest.raises(service.AiCandidateCompareUnavailableError):
        service.get_ai_candidate_compare(_context())


def test_duplicate_assessment_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    left, _right = _ids()
    payload = _valid_payload()
    payload["candidate_assessments"][1]["candidate_id"] = str(left)

    class Provider:
        def generate(self, prompt: str) -> str:
            return AiCandidateCompareLlmPayload.model_validate(payload).model_dump_json()

    monkeypatch.setattr(service, "get_ai_candidate_compare_provider", lambda: Provider())
    with pytest.raises(service.AiCandidateCompareUnavailableError):
        service.get_ai_candidate_compare(_context())


def test_protected_language_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _valid_payload()
    payload["summary"] = "Ask about their marital status before deciding."

    class Provider:
        def generate(self, prompt: str) -> str:
            return AiCandidateCompareLlmPayload.model_validate(payload).model_dump_json()

    monkeypatch.setattr(service, "get_ai_candidate_compare_provider", lambda: Provider())
    with pytest.raises(service.AiCandidateCompareUnavailableError):
        service.get_ai_candidate_compare(_context())


def test_nullable_recommendation_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _valid_payload()
    payload["recommended_candidate_id"] = None
    payload["recommendation_rationale"] = None
    payload["confidence"] = "low"

    class Provider:
        def generate(self, prompt: str) -> str:
            return AiCandidateCompareLlmPayload.model_validate(payload).model_dump_json()

    monkeypatch.setattr(service, "get_ai_candidate_compare_provider", lambda: Provider())
    result = service.get_ai_candidate_compare(_context())
    assert result.recommended_candidate_id is None
    assert result.recommendation_rationale is None


def test_model_generation_mode_is_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _valid_payload()
    raw = AiCandidateCompareLlmPayload.model_validate(payload).model_dump(mode="json")
    raw["generation_mode"] = "live"

    class Provider:
        def generate(self, prompt: str) -> str:
            return __import__("json").dumps(raw)

    monkeypatch.setattr(service, "get_ai_candidate_compare_provider", lambda: Provider())
    result = service.get_ai_candidate_compare(_context(generation_mode="mock"))
    assert result.generation_mode == "mock"


def test_cache_hit_and_no_write_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"count": 0}

    class Provider:
        def generate(self, prompt: str) -> str:
            calls["count"] += 1
            return AiCandidateCompareLlmPayload.model_validate(_valid_payload()).model_dump_json()

    monkeypatch.setattr(service, "get_ai_candidate_compare_provider", lambda: Provider())
    context = _context()
    first = service.get_ai_candidate_compare(context)
    second = service.get_ai_candidate_compare(context)
    assert first.summary == second.summary
    assert calls["count"] == 1

    class Boom:
        def generate(self, prompt: str) -> str:
            raise RuntimeError("fail")

    service.clear_ai_candidate_compare_cache()
    monkeypatch.setattr(service, "get_ai_candidate_compare_provider", lambda: Boom())
    with pytest.raises(service.AiCandidateCompareUnavailableError):
        service.get_ai_candidate_compare(context)
    assert service._cache.get(service._cache_key(context)) is None


def test_cache_identity_is_order_independent_for_sorted_contexts() -> None:
    left, right = _ids()
    context_a = _context()
    # Production build_ai_candidate_compare_context always sorts candidate_ids.
    sorted_ids = tuple(sorted((left, right), key=str))
    assert context_a.candidate_ids == sorted_ids
    twin = service.AiCandidateCompareContext(
        vacancy_id=context_a.vacancy_id,
        candidate_ids=sorted_ids,
        payload=context_a.payload,
        fact_ids=context_a.fact_ids,
        generation_mode=context_a.generation_mode,
    )
    assert service._cache_key(context_a) == service._cache_key(twin)
    assert service._cache_key(context_a) != service._cache_key(
        service.AiCandidateCompareContext(
            vacancy_id=context_a.vacancy_id,
            candidate_ids=sorted_ids,
            payload={"different": True},
            fact_ids=context_a.fact_ids,
            generation_mode=context_a.generation_mode,
        )
    )


def test_cache_not_read_before_provider_when_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ownership/eligibility happen in build_*; get_* only reads cache after that."""
    calls: list[str] = []

    class Provider:
        def generate(self, prompt: str) -> str:
            calls.append("generate")
            return AiCandidateCompareLlmPayload.model_validate(_valid_payload()).model_dump_json()

    monkeypatch.setattr(service, "get_ai_candidate_compare_provider", lambda: Provider())
    service.get_ai_candidate_compare(_context())
    assert calls == ["generate"]


def test_prompt_payload_privacy_excludes_sensitive_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[str] = []

    class Provider:
        def generate(self, prompt: str) -> str:
            captured.append(prompt)
            return AiCandidateCompareLlmPayload.model_validate(_valid_payload()).model_dump_json()

    monkeypatch.setattr(service, "get_ai_candidate_compare_provider", lambda: Provider())
    left, right = _ids()
    payload = {
        "context_version": "ai-candidate-compare-context-v1",
        "vacancy": {
            "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "title": "Backend Engineer",
            "description": "Build APIs",
            "required_skills": ["Python"],
            "preferred_skills": [],
        },
        "candidates": [
            {
                "candidate_id": str(left),
                "candidate_label": "Candidate A",
                "match": {
                    "score": 80,
                    "required_matched": ["Python"],
                    "required_missing": [],
                    "preferred_matched": [],
                    "preferred_missing": [],
                    "score_fact_id": f"candidate:{left}:match-score",
                },
                "passport_summary": {"top_skills": ["Python"], "skills": []},
                "evidence_summaries": [],
            },
            {
                "candidate_id": str(right),
                "candidate_label": "Candidate B",
                "match": {
                    "score": 60,
                    "required_matched": [],
                    "required_missing": ["Python"],
                    "preferred_matched": [],
                    "preferred_missing": [],
                    "score_fact_id": f"candidate:{right}:match-score",
                },
                "passport_summary": {"top_skills": [], "skills": []},
                "evidence_summaries": [],
            },
        ],
        "facts": {
            f"candidate:{left}:match-score": {"type": "match_score", "score": 80},
            f"candidate:{right}:match-score": {"type": "match_score", "score": 60},
            f"candidate:{left}:matched-required:python": {"type": "matched_required"},
            f"candidate:{right}:missing-required:python": {"type": "missing_required"},
            "vacancy:required-skill:python": {"type": "vacancy_required_skill"},
        },
    }
    context = service.AiCandidateCompareContext(
        vacancy_id=uuid4(),
        candidate_ids=(left, right),
        payload=payload,
        fact_ids=frozenset(payload["facts"]),
        generation_mode="live",
    )
    service.get_ai_candidate_compare(context)
    assert len(captured) == 1
    _, marker, serialized = captured[0].partition("\nINPUT:\n")
    assert marker
    input_blob = serialized.casefold()
    forbidden_field_tokens = [
        '"display_name"',
        '"email"',
        '"photo"',
        '"avatar"',
        '"age"',
        '"gender"',
        '"nationality"',
        '"has_note"',
        '"note"',
        '"stage"',
        '"pipeline"',
        "private note",
        "github.com/",
        "scorecard",
        "api_key",
        "authorization",
        "bearer ",
        "jane doe",
        "@example.com",
        "hidden name",
    ]
    for token in forbidden_field_tokens:
        assert token not in input_blob
    assert "candidate a" in input_blob
    assert str(left) in serialized
    assert "hidden name" not in serialized.casefold()


def test_identical_request_reuses_cache_without_second_provider_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"count": 0}

    class Provider:
        def generate(self, prompt: str) -> str:
            calls["count"] += 1
            return AiCandidateCompareLlmPayload.model_validate(_valid_payload()).model_dump_json()

    monkeypatch.setattr(service, "get_ai_candidate_compare_provider", lambda: Provider())
    context = _context(generation_mode="live")
    first = service.get_ai_candidate_compare(context)
    second = service.get_ai_candidate_compare(context)
    assert calls["count"] == 1
    assert first.summary == second.summary
    assert first.generation_mode == "live"
    assert second.generation_mode == "live"


def test_failed_live_response_is_not_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    context = _context(generation_mode="live")

    class Boom:
        def generate(self, prompt: str) -> str:
            raise RuntimeError("upstream failed")

    monkeypatch.setattr(service, "get_ai_candidate_compare_provider", lambda: Boom())
    with pytest.raises(service.AiCandidateCompareUnavailableError):
        service.get_ai_candidate_compare(context)
    assert service._cache.get(service._cache_key(context)) is None
