from collections.abc import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_current_active_user
from app.db.session import get_db
from app.main import app
from app.models.user import User


def make_user(role: str = "candidate") -> User:
    return User(
        id=uuid4(),
        email="user@example.com",
        password_hash="$argon2id$not-public",
        role=role,
        status="active",
    )


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    from app.core.config import settings

    monkeypatch.setattr(settings, "jwt_secret", "stage-3-test-secret-with-32-bytes-minimum")
    app.dependency_overrides[get_db] = lambda: object()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_register_contract_for_candidate_and_employer(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import auth

    monkeypatch.setattr(auth, "register_user", lambda *_args: make_user("candidate"))
    candidate = client.post(
        "/api/v1/auth/register",
        json={"email": "candidate@example.com", "password": "StrongPass123", "role": "candidate"},
    )
    monkeypatch.setattr(auth, "register_user", lambda *_args: make_user("employer"))
    employer = client.post(
        "/api/v1/auth/register",
        json={"email": "employer@example.com", "password": "StrongPass123", "role": "employer"},
    )
    assert candidate.status_code == employer.status_code == 201
    assert set(candidate.json()) == set(employer.json()) == {"id", "email", "role"}


def test_register_rejects_unsupported_role_and_duplicate_email(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import auth
    from app.services.auth import DuplicateEmailError

    invalid_role = client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "StrongPass123", "role": "admin"},
    )

    def duplicate(*_args: object) -> User:
        raise DuplicateEmailError

    monkeypatch.setattr(auth, "register_user", duplicate)
    duplicate_response = client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "StrongPass123", "role": "candidate"},
    )
    assert invalid_role.status_code == 422
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["error"]["code"] == "DUPLICATE_EMAIL"


def test_login_contract_and_identical_invalid_credentials_error(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import auth

    monkeypatch.setattr(auth, "authenticate_user", lambda *_args: make_user())
    success = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "StrongPass123"},
    )
    monkeypatch.setattr(auth, "authenticate_user", lambda *_args: None)
    wrong_password = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "WrongPass123"},
    )
    unknown_email = client.post(
        "/api/v1/auth/login",
        json={"email": "unknown@example.com", "password": "WrongPass123"},
    )
    assert success.status_code == 200
    assert set(success.json()) == {"access_token", "token_type"}
    assert success.json()["token_type"] == "bearer"
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json()["error"]["code"] == unknown_email.json()["error"]["code"]


def test_me_contract_and_missing_token(client: TestClient) -> None:
    app.dependency_overrides[get_current_active_user] = lambda: make_user("candidate")
    success = client.get("/api/v1/me")
    app.dependency_overrides.pop(get_current_active_user)
    missing_token = client.get("/api/v1/me")
    assert success.status_code == 200
    assert set(success.json()) == {"id", "email", "role"}
    assert missing_token.status_code == 401
    assert missing_token.headers["www-authenticate"] == "Bearer"


def test_openapi_contains_stage_three_routes(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()
    assert {
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/api/v1/me",
    }.issubset(schema["paths"])
    assert "password_hash" not in str(schema)
