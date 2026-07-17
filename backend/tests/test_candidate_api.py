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
from app.models.candidate_profile import CandidateProfile
from app.models.user import User


def make_user(role: str = "candidate") -> User:
    return User(
        id=uuid4(),
        email="candidate@example.com",
        password_hash="$argon2id$not-public",
        role=role,
        status="active",
    )


def make_profile(user_id: object | None = None) -> CandidateProfile:
    return CandidateProfile(
        id=uuid4(),
        user_id=user_id or uuid4(),
        full_name="Alan Yerkin",
        headline="Junior Python Backend Developer",
        country="Kazakhstan",
        timezone="Asia/Almaty",
        desired_role="junior_python_backend_developer",
        work_format="remote",
        bio="Short professional biography",
    )


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: object()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def candidate_user() -> User:
    return make_user()


def authorize_candidate(candidate_user: User) -> None:
    app.dependency_overrides[require_candidate] = lambda: candidate_user


def test_get_existing_profile_returns_public_contract(
    client: TestClient, candidate_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import candidate

    authorize_candidate(candidate_user)
    profile = make_profile(candidate_user.id)
    monkeypatch.setattr(candidate, "get_candidate_profile", lambda *_args: profile)

    response = client.get("/api/v1/candidate/profile")

    assert response.status_code == 200
    assert set(response.json()) == {
        "id",
        "full_name",
        "headline",
        "country",
        "timezone",
        "desired_role",
        "work_format",
        "bio",
    }


def test_get_missing_profile_returns_contract_error(
    client: TestClient, candidate_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import candidate

    authorize_candidate(candidate_user)
    monkeypatch.setattr(candidate, "get_candidate_profile", lambda *_args: None)

    response = client.get("/api/v1/candidate/profile")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CANDIDATE_PROFILE_NOT_FOUND"
    assert response.json()["error"]["message"] == "Candidate profile not found"
    assert response.json()["error"]["details"] == []


def test_patch_creates_profile_and_uses_database_default(
    client: TestClient, candidate_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import candidate

    authorize_candidate(candidate_user)
    profile = make_profile(candidate_user.id)
    captured: dict[str, object] = {}

    def patch_profile(*_args: object) -> CandidateProfile:
        captured.update(_args[2])
        return profile

    monkeypatch.setattr(candidate, "patch_candidate_profile", patch_profile)
    response = client.patch("/api/v1/candidate/profile", json={"full_name": "Alan Yerkin"})

    assert response.status_code == 200
    assert "desired_role" not in captured
    assert response.json()["desired_role"] == "junior_python_backend_developer"


def test_patch_updates_only_supplied_fields_and_allows_null(
    client: TestClient, candidate_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import candidate

    authorize_candidate(candidate_user)
    profile = make_profile(candidate_user.id)
    captured: dict[str, object] = {}

    def patch_profile(*_args: object) -> CandidateProfile:
        captured.update(_args[2])
        profile.headline = None
        return profile

    monkeypatch.setattr(candidate, "patch_candidate_profile", patch_profile)
    response = client.patch("/api/v1/candidate/profile", json={"headline": None})

    assert response.status_code == 200
    assert captured == {"headline": None}
    assert response.json()["headline"] is None
    assert response.json()["country"] == "Kazakhstan"


def test_empty_patch_existing_profile_is_allowed(
    client: TestClient, candidate_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import candidate

    authorize_candidate(candidate_user)
    profile = make_profile(candidate_user.id)
    monkeypatch.setattr(candidate, "patch_candidate_profile", lambda *_args: profile)

    response = client.patch("/api/v1/candidate/profile", json={})

    assert response.status_code == 200
    assert response.json()["full_name"] == "Alan Yerkin"


@pytest.mark.parametrize(
    ("payload", "expected_field"),
    [
        ({"full_name": None}, "body"),
        ({"full_name": "   "}, "body.full_name"),
        ({"full_name": "Alan", "desired_role": None}, "body"),
        ({"full_name": "Alan", "desired_role": "   "}, "body.desired_role"),
        ({"full_name": "Alan", "work_format": "office"}, "body.work_format"),
        ({"full_name": "A" * 151}, "body.full_name"),
        ({"full_name": "Alan", "headline": "A" * 161}, "body.headline"),
        ({"full_name": "Alan", "country": "A" * 81}, "body.country"),
        ({"full_name": "Alan", "timezone": "A" * 61}, "body.timezone"),
        ({"full_name": "Alan", "desired_role": "A" * 81}, "body.desired_role"),
        ({"full_name": "Alan", "unknown": "field"}, "body.unknown"),
    ],
)
def test_patch_validation(
    client: TestClient,
    candidate_user: User,
    monkeypatch: pytest.MonkeyPatch,
    payload: dict[str, object],
    expected_field: str,
) -> None:
    from app.api.v1 import candidate

    authorize_candidate(candidate_user)
    patch_service = Mock()
    monkeypatch.setattr(candidate, "patch_candidate_profile", patch_service)

    response = client.patch("/api/v1/candidate/profile", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert any(item["field"] == expected_field for item in response.json()["error"]["details"])
    patch_service.assert_not_called()


def test_patch_missing_full_name_maps_service_error(
    client: TestClient, candidate_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import candidate

    authorize_candidate(candidate_user)
    monkeypatch.setattr(
        candidate,
        "patch_candidate_profile",
        lambda *_args: (_ for _ in ()).throw(candidate.MissingCandidateProfileFullNameError),
    )

    response = client.patch("/api/v1/candidate/profile", json={})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["details"] == [{"field": "full_name", "issue": "missing"}]


def test_patch_database_error_uses_error_envelope(
    client: TestClient, candidate_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import candidate

    authorize_candidate(candidate_user)
    monkeypatch.setattr(
        candidate,
        "patch_candidate_profile",
        lambda *_args: (_ for _ in ()).throw(SQLAlchemyError("database error")),
    )

    response = client.patch("/api/v1/candidate/profile", json={"full_name": "Alan Yerkin"})

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "DATABASE_ERROR"
    assert response.json()["error"]["details"] == []


def test_candidate_profile_requires_candidate_role(client: TestClient) -> None:
    app.dependency_overrides[require_candidate] = lambda: (_ for _ in ()).throw(
        api_error(403, "FORBIDDEN", "Candidate role required")
    )

    response = client.get("/api/v1/candidate/profile")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_candidate_profile_requires_bearer_token(client: TestClient) -> None:
    response = client.get("/api/v1/candidate/profile")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_candidate_profile_openapi_has_only_get_and_patch(client: TestClient) -> None:
    operations = client.get("/openapi.json").json()["paths"]["/api/v1/candidate/profile"]

    assert set(operations) == {"get", "patch"}
    assert "user_id" not in str(operations)
    assert "created_at" not in str(operations)
    assert "updated_at" not in str(operations)
