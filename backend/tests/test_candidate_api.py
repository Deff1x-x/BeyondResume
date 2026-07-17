from collections.abc import Generator
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.api.dependencies import require_candidate
from app.api.errors import api_error
from app.db.session import get_db
from app.main import app
from app.models.candidate_profile import CandidateProfile, OnboardingStatus
from app.models.user import User


def make_user(role: str = "candidate") -> User:
    return User(
        id=uuid4(), email="candidate@example.com", password_hash="hash", role=role, status="active"
    )


def make_profile(user_id: object | None = None) -> CandidateProfile:
    return CandidateProfile(
        id=uuid4(),
        user_id=user_id or uuid4(),
        display_name="Alan Yerkin",
        target_role="Junior developer",
        location="Kazakhstan",
        remote_preference="remote",
        english_level="B2",
        availability="Immediately",
        summary="Summary",
        data_processing_consent=True,
        onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
    )


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: object()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def authorize(user: User) -> None:
    app.dependency_overrides[require_candidate] = lambda: user


def test_candidate_gets_only_own_public_profile(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import candidate

    user = make_user()
    authorize(user)
    monkeypatch.setattr(candidate, "get_candidate_profile", lambda *_args: make_profile(user.id))
    response = client.get("/api/v1/candidate/profile")
    assert response.status_code == 200
    assert "user_id" not in response.json()
    assert "created_at" not in response.json()
    assert response.json()["display_name"] == "Alan Yerkin"


def test_patch_normalizes_only_supplied_fields_and_computes_status(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import candidate

    user = make_user()
    authorize(user)
    profile = make_profile(user.id)
    captured: dict[str, object] = {}

    def patch(*args: object) -> CandidateProfile:
        captured.update(args[2])
        profile.display_name = "Alan"
        return profile

    monkeypatch.setattr(candidate, "patch_candidate_profile", patch)
    response = client.patch("/api/v1/candidate/profile", json={"display_name": "  Alan  "})
    assert response.status_code == 200
    assert captured == {"display_name": "Alan"}
    assert response.json()["onboarding_status"] == "profile_required"


@pytest.mark.parametrize(
    "payload",
    [
        {"portfolio_url": "ftp://example.com"},
        {"display_name": "   "},
        {"onboarding_status": "profile_required"},
        {"user_id": str(uuid4())},
    ],
)
def test_patch_rejects_invalid_or_protected_fields(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, payload: dict[str, object]
) -> None:
    from app.api.v1 import candidate

    authorize(make_user())
    service = Mock()
    monkeypatch.setattr(candidate, "patch_candidate_profile", service)
    response = client.patch("/api/v1/candidate/profile", json=payload)
    assert response.status_code == 422
    service.assert_not_called()


def test_candidate_profile_requires_candidate_role_and_token(client: TestClient) -> None:
    response = client.get("/api/v1/candidate/profile")
    assert response.status_code == 401
    app.dependency_overrides[require_candidate] = lambda: (_ for _ in ()).throw(
        api_error(403, "FORBIDDEN", "Candidate role required")
    )
    assert client.get("/api/v1/candidate/profile").status_code == 403


def test_patch_database_error_does_not_leak_details(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import candidate

    authorize(make_user())
    monkeypatch.setattr(
        candidate,
        "patch_candidate_profile",
        lambda *_args: (_ for _ in ()).throw(SQLAlchemyError("secret")),
    )
    response = client.patch("/api/v1/candidate/profile", json={"display_name": "Alan"})
    assert response.status_code == 500
    assert "secret" not in str(response.json())


def test_candidate_profile_openapi_excludes_internal_fields(client: TestClient) -> None:
    operations = client.get("/openapi.json").json()["paths"]["/api/v1/candidate/profile"]
    assert set(operations) == {"get", "patch"}
    assert all(
        field not in str(operations) for field in ("user_id", "created_at", "updated_at", "audit")
    )


def test_get_missing_profile_returns_contract_error(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import candidate

    authorize(make_user())
    monkeypatch.setattr(candidate, "get_candidate_profile", lambda *_args: None)
    response = client.get("/api/v1/candidate/profile")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CANDIDATE_PROFILE_NOT_FOUND"


def test_empty_patch_preserves_profile(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.v1 import candidate

    user = make_user()
    authorize(user)
    profile = make_profile(user.id)
    monkeypatch.setattr(candidate, "patch_candidate_profile", lambda *_args: profile)
    response = client.patch("/api/v1/candidate/profile", json={})
    assert response.status_code == 200
    assert response.json()["display_name"] == "Alan Yerkin"


@pytest.mark.parametrize("value", [True, False, None])
def test_patch_consent_accepts_explicit_values(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, value: bool | None
) -> None:
    from app.api.v1 import candidate

    user = make_user()
    authorize(user)
    profile = make_profile(user.id)
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        candidate, "patch_candidate_profile", lambda *_args: captured.update(_args[2]) or profile
    )
    response = client.patch("/api/v1/candidate/profile", json={"data_processing_consent": value})
    assert response.status_code == 200
    assert captured == {"data_processing_consent": value}


def test_absent_consent_is_not_updated(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.v1 import candidate

    user = make_user()
    authorize(user)
    profile = make_profile(user.id)
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        candidate, "patch_candidate_profile", lambda *_args: captured.update(_args[2]) or profile
    )
    response = client.patch("/api/v1/candidate/profile", json={"summary": "Updated"})
    assert response.status_code == 200
    assert "data_processing_consent" not in captured


def test_patch_validation_keeps_length_contracts(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import candidate

    authorize(make_user())
    service = Mock()
    monkeypatch.setattr(candidate, "patch_candidate_profile", service)
    for payload in ({"display_name": "A" * 151}, {"target_role": "A" * 81}, {"location": "A" * 81}):
        assert client.patch("/api/v1/candidate/profile", json=payload).status_code == 422
    service.assert_not_called()


def test_patch_missing_profile_returns_not_found(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import candidate

    authorize(make_user())
    monkeypatch.setattr(
        candidate,
        "patch_candidate_profile",
        lambda *_args: (_ for _ in ()).throw(candidate.CandidateProfileNotFoundError),
    )
    response = client.patch("/api/v1/candidate/profile", json={"display_name": "Alan"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CANDIDATE_PROFILE_NOT_FOUND"


def test_patch_explicit_null_does_not_erase_unsupplied_fields(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import candidate

    user = make_user()
    authorize(user)
    profile = make_profile(user.id)
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        candidate, "patch_candidate_profile", lambda *_args: captured.update(_args[2]) or profile
    )
    response = client.patch("/api/v1/candidate/profile", json={"summary": None})
    assert response.status_code == 200
    assert captured == {"summary": None}
    assert response.json()["target_role"] == "Junior developer"


def test_profile_response_contains_only_public_candidate_fields(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import candidate

    user = make_user()
    authorize(user)
    monkeypatch.setattr(candidate, "get_candidate_profile", lambda *_args: make_profile(user.id))
    response = client.get("/api/v1/candidate/profile")
    assert set(response.json()) == {
        "id",
        "display_name",
        "target_role",
        "location",
        "remote_preference",
        "english_level",
        "availability",
        "summary",
        "data_processing_consent",
        "onboarding_status",
        "salary_expectation",
        "preferred_employment_type",
        "relocation_readiness",
        "portfolio_url",
        "linkedin_url",
    }
