from collections.abc import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import require_candidate
from app.api.errors import api_error
from app.db.session import get_db
from app.main import app
from app.models.candidate_profile import CandidateProfile, OnboardingStatus
from app.models.user import User
from app.schemas.evidence import EvidenceHubListResponse


def make_user(role: str = "candidate") -> User:
    return User(
        id=uuid4(),
        email=f"{role}@example.com",
        password_hash="hash",
        role=role,
        status="active",
    )


def make_profile(user_id=None) -> CandidateProfile:
    return CandidateProfile(
        id=uuid4(),
        user_id=user_id or uuid4(),
        display_name="Demo Candidate",
        onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
    )


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: object()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def authorize_candidate(user: User) -> None:
    app.dependency_overrides[require_candidate] = lambda: user


def test_evidence_hub_requires_authentication(client: TestClient) -> None:
    assert client.get("/api/v1/candidate/evidence").status_code == 401


def test_evidence_hub_rejects_employer(client: TestClient) -> None:
    app.dependency_overrides[require_candidate] = lambda: (_ for _ in ()).throw(
        api_error(403, "FORBIDDEN", "Candidate role required")
    )
    assert client.get("/api/v1/candidate/evidence").status_code == 403


def test_evidence_hub_empty_result(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import evidence as evidence_api

    user = make_user()
    profile = make_profile(user.id)
    authorize_candidate(user)
    monkeypatch.setattr(evidence_api, "get_candidate_profile", lambda *_args: profile)
    monkeypatch.setattr(
        evidence_api,
        "list_candidate_evidence",
        lambda *_args, **_kwargs: EvidenceHubListResponse(
            items=[], total=0, limit=20, offset=0
        ),
    )

    response = client.get("/api/v1/candidate/evidence")

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "limit": 20, "offset": 0}


def test_evidence_hub_uses_authenticated_candidate_profile(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import evidence as evidence_api

    user = make_user()
    profile = make_profile(user.id)
    authorize_candidate(user)
    monkeypatch.setattr(evidence_api, "get_candidate_profile", lambda *_args: profile)

    captured: dict[str, object] = {}

    def fake_list(session, candidate_id, query):  # noqa: ANN001
        captured["candidate_id"] = candidate_id
        captured["query"] = query
        return EvidenceHubListResponse(items=[], total=0, limit=query.limit, offset=query.offset)

    monkeypatch.setattr(evidence_api, "list_candidate_evidence", fake_list)

    response = client.get(
        "/api/v1/candidate/evidence",
        params={"candidate_id": str(uuid4()), "source_type": "resume", "limit": 5},
    )

    assert response.status_code == 200
    assert captured["candidate_id"] == profile.id
    assert getattr(captured["query"], "source_type") == "resume"
    assert getattr(captured["query"], "limit") == 5


def test_evidence_hub_profile_not_found(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import evidence as evidence_api

    authorize_candidate(make_user())
    monkeypatch.setattr(evidence_api, "get_candidate_profile", lambda *_args: None)

    response = client.get("/api/v1/candidate/evidence")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROFILE_NOT_FOUND"
