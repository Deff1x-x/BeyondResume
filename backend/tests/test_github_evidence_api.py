from collections.abc import Generator
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import require_candidate
from app.api.errors import api_error
from app.db.session import get_db
from app.main import app
from app.models.candidate_profile import CandidateProfile, OnboardingStatus
from app.models.evidence_unit import EvidenceUnit
from app.models.github_repository import GitHubRepository
from app.models.user import User


def make_user() -> User:
    return User(
        id=uuid4(), email="candidate@example.com", password_hash="hash", role="candidate", status="active"
    )


def make_profile(user_id: UUID | None = None) -> CandidateProfile:
    return CandidateProfile(
        id=uuid4(),
        user_id=user_id or uuid4(),
        display_name="Demo Candidate",
        onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
    )


def make_repository(candidate_id: UUID, repository_id: UUID | None = None) -> GitHubRepository:
    return GitHubRepository(
        id=repository_id or uuid4(),
        candidate_id=candidate_id,
        repository_url="https://github.com/demo-user/demo-api",
        created_at=datetime.now(UTC),
    )


def make_evidence(candidate_id: UUID, repository_url: str) -> EvidenceUnit:
    return EvidenceUnit(
        id=uuid4(),
        candidate_id=candidate_id,
        source_type="github_repository",
        source_reference=repository_url,
        title="GitHub repository: demo-user/demo-api",
        description="Demo repository",
        observed_at=datetime.now(UTC),
        verification_status="source_reachable",
        ownership_status="unverified",
        strength_score=Decimal("1.00"),
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: object()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def authorize_candidate(user: User) -> None:
    app.dependency_overrides[require_candidate] = lambda: user


def test_list_repository_evidence_success(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import github

    user = make_user()
    profile = make_profile(user.id)
    repository = make_repository(profile.id)
    evidence = make_evidence(profile.id, repository.repository_url)
    authorize_candidate(user)
    monkeypatch.setattr(github, "get_candidate_profile", lambda *_args: profile)

    session = Mock()
    session.execute.side_effect = [
        SimpleNamespace(scalar_one_or_none=lambda: repository),
        SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [evidence])),
        SimpleNamespace(
            all=lambda: [
                (
                    evidence.id,
                    "Python",
                    "language",
                    "deterministic",
                    Decimal("1.00"),
                )
            ]
        ),
    ]
    app.dependency_overrides[get_db] = lambda: session

    response = client.get(f"/api/v1/candidate/github/repositories/{repository.id}/evidence")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == str(evidence.id)
    assert body[0]["source_type"] == "github_repository"
    assert body[0]["source_reference"] == repository.repository_url
    assert body[0]["skills"] == [
        {
            "name": "Python",
            "category": "language",
            "extraction_method": "deterministic",
            "evidence_confidence": 1.0,
        }
    ]
    assert "extraction_confidence" not in body[0]["skills"][0]
    assert "confidence" not in body[0]["skills"][0]


def test_list_repository_evidence_not_found(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import github

    user = make_user()
    profile = make_profile(user.id)
    authorize_candidate(user)
    monkeypatch.setattr(github, "get_candidate_profile", lambda *_args: profile)
    session = Mock()
    session.execute.return_value = SimpleNamespace(scalar_one_or_none=lambda: None)
    app.dependency_overrides[get_db] = lambda: session

    response = client.get(f"/api/v1/candidate/github/repositories/{uuid4()}/evidence")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "GITHUB_REPOSITORY_NOT_FOUND"


def test_list_repository_evidence_forbids_foreign_repository(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import github

    user = make_user()
    profile = make_profile(user.id)
    authorize_candidate(user)
    monkeypatch.setattr(github, "get_candidate_profile", lambda *_args: profile)
    # Owned-repository lookup filters by candidate_id; foreign repos look like missing.
    session = Mock()
    session.execute.return_value = SimpleNamespace(scalar_one_or_none=lambda: None)
    app.dependency_overrides[get_db] = lambda: session

    response = client.get(f"/api/v1/candidate/github/repositories/{uuid4()}/evidence")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "GITHUB_REPOSITORY_NOT_FOUND"


def test_list_repository_evidence_requires_candidate_role(client: TestClient) -> None:
    app.dependency_overrides[require_candidate] = lambda: (_ for _ in ()).throw(
        api_error(403, "FORBIDDEN", "Candidate role required")
    )
    response = client.get(f"/api/v1/candidate/github/repositories/{uuid4()}/evidence")
    assert response.status_code == 403
