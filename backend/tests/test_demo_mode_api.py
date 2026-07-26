from collections.abc import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_current_active_user
from app.core.llm_context import force_mock_llm, resolve_llm_provider, set_force_mock_llm
from app.db.session import get_db
from app.main import app
from app.models.user import User
from app.services.demo_users import (
    DEMO_CANDIDATE_EMAIL,
    DEMO_EMPLOYER_EMAIL,
    is_demo_email,
    is_demo_user,
)


def make_demo_user(role: str = "candidate") -> User:
    email = DEMO_EMPLOYER_EMAIL if role == "employer" else DEMO_CANDIDATE_EMAIL
    return User(
        id=uuid4(),
        email=email,
        password_hash="$argon2id$not-public",
        role=role,
        status="active",
    )


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    from app.core.config import settings

    monkeypatch.setattr(settings, "jwt_secret", "demo-mode-test-secret-with-32-bytes-min")
    monkeypatch.setattr(settings, "demo_mode", True)
    app.dependency_overrides[get_db] = lambda: object()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_demo_status_reports_enabled(client: TestClient) -> None:
    response = client.get("/api/v1/demo/status")
    assert response.status_code == 200
    body = response.json()
    assert body["enabled"] is True
    assert body["roles"] == ["candidate", "employer"]


def test_demo_status_reports_disabled(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "demo_mode", False)
    response = client.get("/api/v1/demo/status")
    assert response.status_code == 200
    assert response.json()["enabled"] is False


def test_demo_start_returns_token(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.v1 import demo

    user = make_demo_user("candidate")
    monkeypatch.setattr(demo, "get_demo_user_for_role", lambda *_a, **_k: user)
    monkeypatch.setattr(demo, "create_access_token", lambda *_a, **_k: "demo-access-token")

    response = client.post("/api/v1/demo/start", json={"role": "candidate"})
    assert response.status_code == 200
    assert response.json() == {"access_token": "demo-access-token", "token_type": "bearer"}


def test_demo_start_disabled(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "demo_mode", False)
    response = client.post("/api/v1/demo/start", json={"role": "employer"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DEMO_DISABLED"


def test_demo_reset_requires_demo_user(client: TestClient) -> None:
    regular = User(
        id=uuid4(),
        email="regular@example.com",
        password_hash="$argon2id$not-public",
        role="candidate",
        status="active",
    )
    app.dependency_overrides[get_current_active_user] = lambda: regular
    try:
        response = client.post("/api/v1/demo/reset")
    finally:
        app.dependency_overrides.pop(get_current_active_user, None)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_demo_reset_returns_fresh_token(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.v1 import demo

    user = make_demo_user("employer")
    app.dependency_overrides[get_current_active_user] = lambda: user
    monkeypatch.setattr(demo, "reset_demo_tenants", lambda *_a, **_k: {"employer": user})
    monkeypatch.setattr(demo, "get_demo_user_for_role", lambda *_a, **_k: user)
    monkeypatch.setattr(demo, "create_access_token", lambda *_a, **_k: "reset-token")
    try:
        response = client.post("/api/v1/demo/reset")
    finally:
        app.dependency_overrides.pop(get_current_active_user, None)

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["role"] == "employer"
    assert body["access_token"] == "reset-token"


def test_demo_email_helpers() -> None:
    assert is_demo_email(DEMO_CANDIDATE_EMAIL)
    assert is_demo_email(DEMO_EMPLOYER_EMAIL)
    assert not is_demo_email("person@example.com")
    assert is_demo_user(make_demo_user())
    assert not is_demo_user(
        User(
            id=uuid4(),
            email="person@example.com",
            password_hash="x",
            role="candidate",
            status="active",
        )
    )


def test_force_mock_llm_overrides_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "llm_provider", "openai")
    set_force_mock_llm(False)
    assert resolve_llm_provider() == "openai"
    set_force_mock_llm(True)
    assert resolve_llm_provider() == "mock"
    with force_mock_llm(True):
        assert resolve_llm_provider() == "mock"
    set_force_mock_llm(False)
    assert resolve_llm_provider() == "openai"


def test_demo_access_token_claim(monkeypatch: pytest.MonkeyPatch) -> None:
    from uuid import uuid4

    from app.core.config import settings
    from app.core.security import access_token_is_demo, create_access_token

    monkeypatch.setattr(settings, "jwt_secret", "demo-mode-test-secret-with-32-bytes-min")
    regular = create_access_token(uuid4())
    demo = create_access_token(uuid4(), demo=True)
    assert access_token_is_demo(regular) is False
    assert access_token_is_demo(demo) is True
