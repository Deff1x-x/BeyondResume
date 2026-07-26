"""One-off live/failure smoke for AI Candidate Compare.

Does not print secrets. Not part of the default pytest suite.
Run:
  .venv/Scripts/python.exe scripts/ai_candidate_compare_live_smoke.py live
  .venv/Scripts/python.exe scripts/ai_candidate_compare_live_smoke.py failure
"""

from __future__ import annotations

import json
import sys
from collections.abc import Generator
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.api.dependencies import require_employer  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.db.session import engine, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.candidate_profile import CandidateProfile, OnboardingStatus  # noqa: E402
from app.models.employer_candidate_shortlist import EmployerCandidateShortlist  # noqa: E402
from app.models.employer_profile import EmployerProfile  # noqa: E402
from app.models.skill import Skill  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.vacancy import Vacancy  # noqa: E402
from app.models.vacancy_skill_requirement import VacancySkillRequirement  # noqa: E402
from app.services import ai_candidate_compare as compare_service  # noqa: E402


def _safe_print(label: str, value: object) -> None:
    text = str(value)
    lowered = text.casefold()
    if "sk-" in lowered or "bearer " in lowered or "api_key=" in lowered:
        raise RuntimeError("Refusing to print a value that looks like a secret")
    print(f"{label}={value}")


class _Cleanup:
    def __init__(self, client: TestClient, transaction: object, connection: object) -> None:
        self.client = client
        self.transaction = transaction
        self.connection = connection

    def close(self) -> None:
        self.client.close()
        app.dependency_overrides.clear()
        self.transaction.rollback()  # type: ignore[attr-defined]
        self.connection.close()  # type: ignore[attr-defined]


def _build_client() -> tuple[TestClient, tuple[str, str, str], _Cleanup]:
    try:
        connection = engine.connect()
    except SQLAlchemyError as error:
        raise SystemExit(f"PostgreSQL unavailable: {error}") from error

    transaction = connection.begin()
    setup = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )
    employer_user = User(
        id=uuid4(),
        email=f"smoke-employer-{uuid4()}@example.com",
        password_hash="hash",
        role="employer",
        status="active",
    )
    employer = EmployerProfile(
        id=uuid4(), user_id=employer_user.id, company_name="Smoke Employer"
    )
    vacancy = Vacancy(
        id=uuid4(),
        employer_id=employer.id,
        title="Backend Engineer",
        description="Build employer-safe APIs.",
        status="open",
    )
    candidate_users = [
        User(
            id=uuid4(),
            email=f"smoke-candidate-{uuid4()}@example.com",
            password_hash="hash",
            role="candidate",
            status="active",
        )
        for _ in range(2)
    ]
    candidates = [
        CandidateProfile(
            id=uuid4(),
            user_id=user.id,
            display_name=f"Smoke Candidate {index}",
            onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
        )
        for index, user in enumerate(candidate_users, start=1)
    ]
    skill = Skill(
        id=uuid4(),
        canonical_name=f"Python-{uuid4().hex[:8]}",
        normalized_name=f"python-{uuid4().hex[:8]}",
        category="backend",
        ontology_version="test",
        deprecated=False,
    )
    requirement = VacancySkillRequirement(
        id=uuid4(),
        vacancy_id=vacancy.id,
        skill_id=skill.id,
        requirement_type="required",
    )
    shortlists = [
        EmployerCandidateShortlist(
            id=uuid4(),
            employer_id=employer.id,
            vacancy_id=vacancy.id,
            candidate_id=candidate.id,
            stage="shortlisted",
        )
        for candidate in candidates
    ]
    setup.add_all([employer_user, *candidate_users, employer, vacancy, *candidates, skill])
    setup.flush()
    setup.add_all([requirement, *shortlists])
    setup.commit()
    setup.close()

    def request_session() -> Generator[Session, None, None]:
        session = Session(bind=connection, join_transaction_mode="create_savepoint")
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = request_session
    app.dependency_overrides[require_employer] = lambda: employer_user
    client = TestClient(app)
    ids = (str(vacancy.id), str(candidates[0].id), str(candidates[1].id))
    return client, ids, _Cleanup(client, transaction, connection)


def _summarize_success(
    response_status: int, body: dict[str, object], provider_calls: int
) -> dict[str, object]:
    assessments = body.get("candidate_assessments") or []
    assert isinstance(assessments, list)
    fact_ref_count = 0
    for assessment in assessments:
        if not isinstance(assessment, dict):
            continue
        for key in ("strengths", "risks"):
            for insight in assessment.get(key) or []:
                if isinstance(insight, dict):
                    fact_ref_count += len(insight.get("fact_refs") or [])
    for key in ("key_differences", "uncertainties"):
        for insight in body.get(key) or []:
            if isinstance(insight, dict):
                fact_ref_count += len(insight.get("fact_refs") or [])
    for question in body.get("interview_focus_questions") or []:
        if isinstance(question, dict):
            fact_ref_count += len(question.get("fact_refs") or [])
    rationale = body.get("recommendation_rationale")
    if isinstance(rationale, dict):
        fact_ref_count += len(rationale.get("fact_refs") or [])

    summary = str(body.get("summary") or "")
    truncated = summary if len(summary) <= 180 else summary[:177] + "..."
    error = body.get("error")
    error_code = error.get("code") if isinstance(error, dict) else None
    return {
        "http_status": response_status,
        "generation_mode": body.get("generation_mode"),
        "candidate_count": len(body.get("candidate_ids") or []),
        "summary_preview": truncated,
        "assessment_count": len(assessments),
        "recommendation_present": body.get("recommended_candidate_id") is not None,
        "confidence": body.get("confidence"),
        "grounded_fact_ref_count": fact_ref_count,
        "provider_generate_calls": provider_calls,
        "error_code": error_code,
        "semantic_validation_passed": (
            response_status == 200
            and body.get("generation_mode") == "live"
            and len(assessments) >= 2
            and fact_ref_count > 0
        ),
        "demo_ai_badge_expected": False,
    }


def run_live() -> dict[str, object]:
    if settings.llm_provider != "openai":
        raise SystemExit(f"Expected llm_provider=openai, got {settings.llm_provider!r}")
    if not settings.llm_api_key.strip():
        raise SystemExit("LLM_API_KEY is empty")

    compare_service.clear_ai_candidate_compare_cache()
    client, (vacancy_id, left, right), cleanup = _build_client()
    try:
        from app.integrations import openai_ai_candidate_compare as openai_module

        provider_calls = {"count": 0}
        original_generate = openai_module.OpenAIAiCandidateCompareProvider.generate

        def counted_generate(self: object, prompt: str) -> str:
            provider_calls["count"] += 1
            return original_generate(self, prompt)  # type: ignore[misc]

        openai_module.OpenAIAiCandidateCompareProvider.generate = counted_generate  # type: ignore[method-assign]
        try:
            response = client.post(
                f"/api/v1/employer/vacancies/{vacancy_id}/ai-compare",
                json={"candidate_ids": [left, right]},
            )
        finally:
            openai_module.OpenAIAiCandidateCompareProvider.generate = original_generate  # type: ignore[method-assign]

        body = response.json() if response.content else {}
        return _summarize_success(response.status_code, body, provider_calls["count"])
    finally:
        cleanup.close()


def run_failure() -> dict[str, object]:
    """Injected openai-provider failure; no mock fallback."""
    compare_service.clear_ai_candidate_compare_cache()
    client, (vacancy_id, left, right), cleanup = _build_client()
    try:
        from app.integrations import ai_candidate_compare as factory
        from app.integrations.openai_ai_candidate_compare import (
            OpenAIAiCandidateCompareProviderError,
        )

        original_get = factory.get_ai_candidate_compare_provider
        original_provider = settings.llm_provider
        original_key = settings.llm_api_key
        settings.llm_provider = "openai"
        # Keep a non-empty key so openai mode is selected; never print it.
        settings.llm_api_key = "sk-invalid-local-smoke-key"

        class FailingOpenAIProvider:
            provider_name = "openai"

            def generate(self, prompt: str) -> str:
                raise OpenAIAiCandidateCompareProviderError(
                    "OpenAI request failed (AuthenticationError)"
                )

        factory.get_ai_candidate_compare_provider = lambda: FailingOpenAIProvider()  # type: ignore[assignment]
        try:
            assert settings.llm_provider == "openai"
            response = client.post(
                f"/api/v1/employer/vacancies/{vacancy_id}/ai-compare",
                json={"candidate_ids": [left, right]},
            )
            body = response.json() if response.content else {}
            error = body.get("error")
            return {
                "http_status": response.status_code,
                "error_code": error.get("code") if isinstance(error, dict) else None,
                "has_summary": "summary" in body,
                "generation_mode": body.get("generation_mode"),
                "provider_remained_openai": settings.llm_provider == "openai",
                "no_mock_fallback": body.get("generation_mode") != "mock",
            }
        finally:
            factory.get_ai_candidate_compare_provider = original_get  # type: ignore[assignment]
            settings.llm_provider = original_provider
            settings.llm_api_key = original_key
    finally:
        cleanup.close()


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "live"
    _safe_print("configured_provider", settings.llm_provider)
    _safe_print("configured_model", settings.llm_model)
    _safe_print("api_key_configured", bool(settings.llm_api_key.strip()))
    result = run_failure() if mode == "failure" else run_live()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
