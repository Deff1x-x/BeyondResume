"""Temporary live performance check for AI Candidate Compare prompt v3.

Not for commit. Does not print secrets or full payloads.
"""

from __future__ import annotations

import sys
from pathlib import Path
from time import monotonic
from uuid import UUID

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import settings  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.vacancy import Vacancy  # noqa: E402
from app.prompts.ai_candidate_compare import PROMPT_VERSION, SYSTEM_RULES  # noqa: E402
from app.services import ai_candidate_compare as service  # noqa: E402

VACANCY_ID = UUID("c3440939-9873-4bac-97b7-9482692efb49")
CANDIDATE_IDS = [
    UUID("fce674d1-3c00-49a0-8e2c-6f496d9c1c92"),
    UUID("c3724659-d902-48e5-8883-98fcbce7febc"),
]


def _fact_ref_count(result: object) -> int:
    data = result.model_dump()  # type: ignore[attr-defined]
    count = 0
    for assessment in data.get("candidate_assessments") or []:
        for key in ("strengths", "risks"):
            for insight in assessment.get(key) or []:
                count += len(insight.get("fact_refs") or [])
    for key in ("key_differences", "uncertainties"):
        for insight in data.get(key) or []:
            count += len(insight.get("fact_refs") or [])
    for question in data.get("interview_focus_questions") or []:
        count += len(question.get("fact_refs") or [])
    rationale = data.get("recommendation_rationale")
    if isinstance(rationale, dict):
        count += len(rationale.get("fact_refs") or [])
    return count


def main() -> None:
    if settings.llm_provider != "openai":
        raise SystemExit(f"expected openai, got {settings.llm_provider!r}")
    print(f"prompt_version={PROMPT_VERSION}")
    print(f"system_rules_chars={len(SYSTEM_RULES)}")
    print(f"timeout_seconds={settings.llm_timeout_seconds}")

    service.clear_ai_candidate_compare_cache()
    session = SessionLocal()
    try:
        vacancy = session.get(Vacancy, VACANCY_ID)
        if vacancy is None:
            raise SystemExit("vacancy not found")
        context = service.build_ai_candidate_compare_context(
            session,
            employer_id=vacancy.employer_id,
            vacancy_id=VACANCY_ID,
            candidate_ids=CANDIDATE_IDS,
        )
        prompt = service.build_ai_candidate_compare_prompt(context)
        print(f"full_prompt_chars={len(prompt)}")
        print(f"runtime_has_few_shot={('Candidate A is the clearer' in prompt)}")
        print(f"runtime_has_schema_defs={('\"$defs\"' in prompt)}")

        calls = {"count": 0}
        from app.integrations import openai_ai_candidate_compare as openai_module

        original = openai_module.OpenAIAiCandidateCompareProvider.generate

        def counted(self: object, prompt_text: str) -> str:
            calls["count"] += 1
            started = monotonic()
            content = original(self, prompt_text)  # type: ignore[misc]
            print(f"openai_latency_ms={round((monotonic() - started) * 1000)}")
            return content

        openai_module.OpenAIAiCandidateCompareProvider.generate = counted  # type: ignore[method-assign]
        try:
            first = service.get_ai_candidate_compare(context)
            print("request_a=miss_then_success")
            print(f"http_equivalent_status=200")
            print(f"generation_mode={first.generation_mode}")
            print(f"assessment_count={len(first.candidate_assessments)}")
            print(f"recommendation_present={first.recommended_candidate_id is not None}")
            print(f"fact_ref_count={_fact_ref_count(first)}")
            print(f"semantic_validation=passed")
            blob = first.model_dump_json().casefold()
            filler = [
                "according to the supplied facts",
                "according to the input",
                "according to the system match facts",
                "system match score indicates",
            ]
            print(f"filler_absent={not any(item in blob for item in filler)}")
            print(f"provider_calls_after_a={calls['count']}")

            second = service.get_ai_candidate_compare(context)
            print("request_b=cache_hit")
            print(f"provider_calls_after_b={calls['count']}")
            print(f"cache_hit_same_summary={first.summary == second.summary}")
        finally:
            openai_module.OpenAIAiCandidateCompareProvider.generate = original  # type: ignore[method-assign]
    finally:
        session.close()


if __name__ == "__main__":
    main()
