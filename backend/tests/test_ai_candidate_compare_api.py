"""API contract tests for AI Candidate Compare."""

from __future__ import annotations

from collections.abc import Callable, Generator
from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.dependencies import require_employer
from app.db.session import engine, get_db
from app.main import app
from app.models.candidate_profile import CandidateProfile, OnboardingStatus
from app.models.employer_candidate_shortlist import EmployerCandidateShortlist
from app.models.employer_profile import EmployerProfile
from app.models.skill import Skill
from app.models.user import User
from app.models.vacancy import Vacancy
from app.models.vacancy_skill_requirement import VacancySkillRequirement
from app.schemas.ai_candidate_compare import AiCandidateCompareResponse
from app.services.ai_candidate_compare import (
    AiCandidateCompareCandidateNotFoundError,
    AiCandidateCompareUnavailableError,
    AiCandidateCompareVacancyNotFoundError,
)


@dataclass(frozen=True)
class CompareApiContext:
    employer_user: User
    other_employer_user: User
    employer: EmployerProfile
    other_employer: EmployerProfile
    vacancy: Vacancy
    foreign_vacancy: Vacancy
    candidate_ids: tuple[UUID, UUID, UUID]
    ineligible_candidate_id: UUID
    non_shortlisted_candidate_id: UUID
    new_session: Callable[[], Session]


def _sample_response(vacancy_id: UUID, candidate_ids: list[UUID]) -> AiCandidateCompareResponse:
    left, right = candidate_ids[0], candidate_ids[1]
    return AiCandidateCompareResponse.model_validate(
        {
            "vacancy_id": str(vacancy_id),
            "candidate_ids": [str(item) for item in sorted(candidate_ids, key=str)[:2]],
            "generation_mode": "mock",
            "summary": "Relative comparison based on supplied facts.",
            "candidate_assessments": [
                {
                    "candidate_id": str(left),
                    "strengths": [
                        {
                            "text": "Stronger required coverage.",
                            "fact_refs": [f"candidate:{left}:match-score"],
                        }
                    ],
                    "risks": [
                        {
                            "text": "Limited preferred coverage.",
                            "fact_refs": [f"candidate:{left}:match-score"],
                        }
                    ],
                },
                {
                    "candidate_id": str(right),
                    "strengths": [
                        {
                            "text": "Comparable match score available.",
                            "fact_refs": [f"candidate:{right}:match-score"],
                        }
                    ],
                    "risks": [
                        {
                            "text": "Weaker required coverage.",
                            "fact_refs": [f"candidate:{right}:match-score"],
                        }
                    ],
                },
            ],
            "key_differences": [
                {
                    "text": "Required skill coverage differs.",
                    "fact_refs": [
                        f"candidate:{left}:match-score",
                        f"candidate:{right}:match-score",
                    ],
                }
            ],
            "interview_focus_questions": [
                {
                    "question": "Describe a production service you owned.",
                    "candidate_ids": [str(left)],
                    "fact_refs": [f"candidate:{left}:match-score"],
                }
            ],
            "recommended_candidate_id": None,
            "recommendation_rationale": None,
            "confidence": "low",
            "uncertainties": [
                {
                    "text": "Evidence depth is limited.",
                    "fact_refs": [f"candidate:{left}:match-score"],
                }
            ],
        }
    )


@pytest.fixture
def compare_client() -> Generator[tuple[TestClient, CompareApiContext], None, None]:
    try:
        connection = engine.connect()
    except SQLAlchemyError as error:
        pytest.skip(f"PostgreSQL is unavailable: {error}")

    transaction = connection.begin()
    setup = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )
    employer_user = User(
        id=uuid4(),
        email=f"compare-employer-{uuid4()}@example.com",
        password_hash="hash",
        role="employer",
        status="active",
    )
    other_employer_user = User(
        id=uuid4(),
        email=f"compare-other-{uuid4()}@example.com",
        password_hash="hash",
        role="employer",
        status="active",
    )
    employer = EmployerProfile(
        id=uuid4(), user_id=employer_user.id, company_name="Compare Employer"
    )
    other_employer = EmployerProfile(
        id=uuid4(), user_id=other_employer_user.id, company_name="Other Employer"
    )
    vacancy = Vacancy(
        id=uuid4(), employer_id=employer.id, title="Backend Engineer", status="open"
    )
    foreign_vacancy = Vacancy(
        id=uuid4(), employer_id=other_employer.id, title="Foreign Role", status="open"
    )
    candidate_users = [
        User(
            id=uuid4(),
            email=f"compare-candidate-{uuid4()}@example.com",
            password_hash="hash",
            role="candidate",
            status="active",
        )
        for _ in range(4)
    ]
    candidates = [
        CandidateProfile(
            id=uuid4(),
            user_id=user.id,
            display_name=f"Candidate {index}",
            onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
        )
        for index, user in enumerate(candidate_users[:3], start=1)
    ]
    ineligible = CandidateProfile(
        id=uuid4(),
        user_id=candidate_users[3].id,
        display_name=None,
        onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
    )
    non_shortlisted_user = User(
        id=uuid4(),
        email=f"compare-nonshort-{uuid4()}@example.com",
        password_hash="hash",
        role="candidate",
        status="active",
    )
    non_shortlisted = CandidateProfile(
        id=uuid4(),
        user_id=non_shortlisted_user.id,
        display_name="Not Shortlisted",
        onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
    )
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

    setup.add_all(
        [
            employer_user,
            other_employer_user,
            *candidate_users,
            non_shortlisted_user,
            employer,
            other_employer,
            vacancy,
            foreign_vacancy,
            *candidates,
            ineligible,
            non_shortlisted,
            skill,
        ]
    )
    setup.flush()
    setup.add_all([requirement, *shortlists])
    setup.commit()
    setup.close()

    def new_session() -> Session:
        return Session(bind=connection, join_transaction_mode="create_savepoint")

    def request_session() -> Generator[Session, None, None]:
        session = new_session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = request_session
    app.dependency_overrides[require_employer] = lambda: employer_user
    context = CompareApiContext(
        employer_user=employer_user,
        other_employer_user=other_employer_user,
        employer=employer,
        other_employer=other_employer,
        vacancy=vacancy,
        foreign_vacancy=foreign_vacancy,
        candidate_ids=(candidates[0].id, candidates[1].id, candidates[2].id),
        ineligible_candidate_id=ineligible.id,
        non_shortlisted_candidate_id=non_shortlisted.id,
        new_session=new_session,
    )
    with TestClient(app) as client:
        yield client, context
    app.dependency_overrides.clear()
    transaction.rollback()
    connection.close()


def test_ai_compare_success(
    compare_client: tuple[TestClient, CompareApiContext],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.api.v1 import employer

    client, ctx = compare_client
    selected = [ctx.candidate_ids[0], ctx.candidate_ids[1]]
    monkeypatch.setattr(
        employer,
        "build_ai_candidate_compare_context",
        lambda *_args, **_kwargs: object(),
    )
    monkeypatch.setattr(
        employer,
        "get_ai_candidate_compare",
        lambda _context: _sample_response(ctx.vacancy.id, selected),
    )

    response = client.post(
        f"/api/v1/employer/vacancies/{ctx.vacancy.id}/ai-compare",
        json={"candidate_ids": [str(item) for item in selected]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["generation_mode"] == "mock"
    assert body["recommended_candidate_id"] is None
    assert len(body["candidate_assessments"]) == 2


def test_ai_compare_foreign_vacancy_404(
    compare_client: tuple[TestClient, CompareApiContext],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.api.v1 import employer

    client, ctx = compare_client

    def boom(*_args: object, **_kwargs: object) -> object:
        raise AiCandidateCompareVacancyNotFoundError

    monkeypatch.setattr(employer, "build_ai_candidate_compare_context", boom)
    response = client.post(
        f"/api/v1/employer/vacancies/{ctx.foreign_vacancy.id}/ai-compare",
        json={
            "candidate_ids": [str(ctx.candidate_ids[0]), str(ctx.candidate_ids[1])],
        },
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "VACANCY_NOT_FOUND"


def test_ai_compare_candidate_not_found(
    compare_client: tuple[TestClient, CompareApiContext],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.api.v1 import employer

    client, ctx = compare_client

    def boom(*_args: object, **_kwargs: object) -> object:
        raise AiCandidateCompareCandidateNotFoundError

    monkeypatch.setattr(employer, "build_ai_candidate_compare_context", boom)
    response = client.post(
        f"/api/v1/employer/vacancies/{ctx.vacancy.id}/ai-compare",
        json={
            "candidate_ids": [
                str(ctx.candidate_ids[0]),
                str(ctx.non_shortlisted_candidate_id),
            ],
        },
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CANDIDATE_NOT_FOUND"


def test_ai_compare_unavailable_503(
    compare_client: tuple[TestClient, CompareApiContext],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.api.v1 import employer

    client, ctx = compare_client
    monkeypatch.setattr(
        employer,
        "build_ai_candidate_compare_context",
        lambda *_args, **_kwargs: object(),
    )

    def boom(_context: object) -> object:
        raise AiCandidateCompareUnavailableError

    monkeypatch.setattr(employer, "get_ai_candidate_compare", boom)
    response = client.post(
        f"/api/v1/employer/vacancies/{ctx.vacancy.id}/ai-compare",
        json={
            "candidate_ids": [str(ctx.candidate_ids[0]), str(ctx.candidate_ids[1])],
        },
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "AI_CANDIDATE_COMPARE_UNAVAILABLE"


@pytest.mark.parametrize(
    "candidate_ids",
    [
        [],
        [str(uuid4())],
        [str(uuid4()) for _ in range(5)],
    ],
)
def test_ai_compare_size_validation(
    compare_client: tuple[TestClient, CompareApiContext],
    candidate_ids: list[str],
) -> None:
    client, ctx = compare_client
    response = client.post(
        f"/api/v1/employer/vacancies/{ctx.vacancy.id}/ai-compare",
        json={"candidate_ids": candidate_ids},
    )
    assert response.status_code == 422


def test_ai_compare_duplicate_ids_rejected(
    compare_client: tuple[TestClient, CompareApiContext],
) -> None:
    client, ctx = compare_client
    candidate_id = str(ctx.candidate_ids[0])
    response = client.post(
        f"/api/v1/employer/vacancies/{ctx.vacancy.id}/ai-compare",
        json={"candidate_ids": [candidate_id, candidate_id]},
    )
    assert response.status_code == 422


def test_ai_compare_end_to_end_with_mock_provider(
    compare_client: tuple[TestClient, CompareApiContext],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.integrations import ai_candidate_compare as factory

    client, ctx = compare_client
    monkeypatch.setattr(factory.settings, "llm_provider", "mock")
    response = client.post(
        f"/api/v1/employer/vacancies/{ctx.vacancy.id}/ai-compare",
        json={
            "candidate_ids": [str(ctx.candidate_ids[1]), str(ctx.candidate_ids[0])],
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["generation_mode"] == "mock"
    assert body["vacancy_id"] == str(ctx.vacancy.id)
    assert body["candidate_ids"] == sorted(
        [str(ctx.candidate_ids[0]), str(ctx.candidate_ids[1])]
    )
    assert len(body["candidate_assessments"]) == 2


def test_ai_compare_ineligible_and_non_shortlisted_return_404(
    compare_client: tuple[TestClient, CompareApiContext],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.integrations import ai_candidate_compare as factory

    client, ctx = compare_client
    monkeypatch.setattr(factory.settings, "llm_provider", "mock")

    ineligible = client.post(
        f"/api/v1/employer/vacancies/{ctx.vacancy.id}/ai-compare",
        json={
            "candidate_ids": [
                str(ctx.candidate_ids[0]),
                str(ctx.ineligible_candidate_id),
            ],
        },
    )
    assert ineligible.status_code == 404
    assert ineligible.json()["error"]["code"] == "CANDIDATE_NOT_FOUND"

    non_shortlisted = client.post(
        f"/api/v1/employer/vacancies/{ctx.vacancy.id}/ai-compare",
        json={
            "candidate_ids": [
                str(ctx.candidate_ids[0]),
                str(ctx.non_shortlisted_candidate_id),
            ],
        },
    )
    assert non_shortlisted.status_code == 404
    assert non_shortlisted.json()["error"]["code"] == "CANDIDATE_NOT_FOUND"


def test_ai_compare_cache_hit_is_order_independent_and_authz_still_runs(
    compare_client: tuple[TestClient, CompareApiContext],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.integrations import ai_candidate_compare as factory
    from app.integrations.mock_ai_candidate_compare import MockAiCandidateCompareProvider
    from app.services import ai_candidate_compare as compare_service

    client, ctx = compare_client
    monkeypatch.setattr(factory.settings, "llm_provider", "mock")
    compare_service.clear_ai_candidate_compare_cache()
    calls = {"count": 0}
    original_generate = MockAiCandidateCompareProvider.generate

    def counted_generate(self: MockAiCandidateCompareProvider, prompt: str) -> str:
        calls["count"] += 1
        return original_generate(self, prompt)

    monkeypatch.setattr(MockAiCandidateCompareProvider, "generate", counted_generate)

    first = client.post(
        f"/api/v1/employer/vacancies/{ctx.vacancy.id}/ai-compare",
        json={
            "candidate_ids": [str(ctx.candidate_ids[0]), str(ctx.candidate_ids[1])],
        },
    )
    second = client.post(
        f"/api/v1/employer/vacancies/{ctx.vacancy.id}/ai-compare",
        json={
            "candidate_ids": [str(ctx.candidate_ids[1]), str(ctx.candidate_ids[0])],
        },
    )
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["summary"] == second.json()["summary"]
    assert first.json()["candidate_ids"] == second.json()["candidate_ids"]
    assert calls["count"] == 1

    # Authz/eligibility still applied on the cache-hit path via build_context.
    blocked = client.post(
        f"/api/v1/employer/vacancies/{ctx.vacancy.id}/ai-compare",
        json={
            "candidate_ids": [
                str(ctx.candidate_ids[0]),
                str(ctx.ineligible_candidate_id),
            ],
        },
    )
    assert blocked.status_code == 404
    assert blocked.json()["error"]["code"] == "CANDIDATE_NOT_FOUND"
