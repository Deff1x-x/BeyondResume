"""Prompt contract tests for AI Candidate Compare."""

from __future__ import annotations

import json

from app.prompts import ai_candidate_compare as prompt_module
from app.schemas.ai_candidate_compare import AiCandidateCompareLlmPayload
from app.services.ai_candidate_compare import (
    AiCandidateCompareContext,
    build_ai_candidate_compare_prompt,
)
from uuid import UUID, uuid4


def test_prompt_version_is_v6() -> None:
    assert prompt_module.PROMPT_VERSION == "ai-candidate-compare-v6"


def test_prompt_examples_validate_against_dto() -> None:
    AiCandidateCompareLlmPayload.model_validate_json(prompt_module.COMPLETE_EXAMPLE_JSON)
    AiCandidateCompareLlmPayload.model_validate_json(prompt_module.CLOSE_RACE_EXAMPLE_JSON)


def test_system_rules_remain_compact_and_include_required_guidance() -> None:
    rules = prompt_module.SYSTEM_RULES
    assert len(rules) <= prompt_module.MAX_SYSTEM_RULES_CHARS
    assert len(rules) < 5000

    lowered = rules.casefold()
    required_fragments = [
        "hiring manager",
        "cto",
        "comparison table is already visible",
        "source of truth",
        "not to explain the table",
        "not obvious",
        "do not write it",
        "fact_refs",
        "do not invent",
        "match scores",
        "protected",
        "personality",
        "pipeline",
        "according to the supplied facts",
        "summary",
        "strengths",
        "risks",
        "key_differences",
        "interview_focus_questions",
        "uncertainties",
        "hiring_recommendation",
        "current leader",
        "no clear recommendation",
        "brevity",
        "at most 2 strengths",
        "strongest fact_refs",
        "flip today's recommendation",
    ]
    for fragment in required_fragments:
        assert fragment in lowered, fragment


def test_runtime_prompt_excludes_full_schema_and_few_shot_fixtures() -> None:
    left = UUID("11111111-1111-1111-1111-111111111111")
    right = UUID("22222222-2222-2222-2222-222222222222")
    context = AiCandidateCompareContext(
        vacancy_id=uuid4(),
        candidate_ids=(left, right),
        payload={
            "vacancy": {"id": str(uuid4()), "title": "Backend"},
            "candidates": [
                {"candidate_id": str(left), "candidate_label": "Candidate A"},
                {"candidate_id": str(right), "candidate_label": "Candidate B"},
            ],
            "facts": {},
        },
        fact_ids=frozenset(),
        generation_mode="live",
    )
    prompt = build_ai_candidate_compare_prompt(context)
    schema_blob = json.dumps(prompt_module.RESPONSE_JSON_SCHEMA)
    assert schema_blob not in prompt
    assert '"$defs"' not in prompt
    assert prompt_module.COMPLETE_EXAMPLE_JSON not in prompt
    assert prompt_module.CLOSE_RACE_EXAMPLE_JSON not in prompt
    assert "\nINPUT:\n" in prompt
    assert prompt.startswith(prompt_module.SYSTEM_RULES)
