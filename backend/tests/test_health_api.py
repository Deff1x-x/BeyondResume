from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.db.session import get_db
from app.main import app


class _ReadySession:
    def execute(self, *_args: object, **_kwargs: object) -> None:
        return None


class _FailingSession:
    def execute(self, *_args: object, **_kwargs: object) -> None:
        raise OperationalError("SELECT 1", {}, Exception("database unavailable"))


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_returns_ok_when_database_is_ready(client: TestClient) -> None:
    app.dependency_overrides[get_db] = lambda: _ReadySession()

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ready"}


def test_health_does_not_report_ready_when_database_fails(client: TestClient) -> None:
    app.dependency_overrides[get_db] = lambda: _FailingSession()

    response = client.get("/api/v1/health")

    assert response.status_code == 503
    body = response.json()
    assert body.get("status") != "ok"
    assert body.get("database") != "ready"
    assert "error" in body
    assert body["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert "password" not in response.text.lower()
    assert "database_url" not in response.text.lower()
