"""Static deployment contract for docker-compose.yml without a YAML parser."""

from __future__ import annotations

import re
from pathlib import Path

_COMPOSE = Path(__file__).resolve().parents[2] / "docker-compose.yml"
_SERVICE_HEADER = re.compile(r"^  [A-Za-z0-9_-]+:\s*$", re.MULTILINE)
_TOP_LEVEL = re.compile(r"^[A-Za-z0-9_-]+:\s*$", re.MULTILINE)


def _normalize(text: str) -> str:
    # Normalize CRLF from Windows checkout so assertions stay portable.
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _service_block(text: str, service_name: str) -> str:
    marker = f"  {service_name}:"
    start = text.index(marker)
    following = [
        match.start()
        for match in _SERVICE_HEADER.finditer(text, start + len(marker))
        if match.group(0).strip() != f"{service_name}:"
    ]
    top_level = [
        match.start()
        for match in _TOP_LEVEL.finditer(text, start + len(marker))
        if match.start() > start
    ]
    candidates = following + top_level
    end = min(candidates) if candidates else len(text)
    return text[start:end]


def _read_compose() -> str:
    return _normalize(_COMPOSE.read_text(encoding="utf-8"))


def test_compose_backend_waits_for_healthy_postgres_with_persistent_volume() -> None:
    text = _read_compose()
    backend = _service_block(text, "backend")
    postgres = _service_block(text, "postgres")

    assert "depends_on:\n      postgres:\n        condition: service_healthy" in backend
    assert re.search(r"(?m)^\s+depends_on:\s*\n\s+-\s+postgres\s*$", backend) is None
    assert "--reload" not in backend
    assert "restart: unless-stopped" in backend
    assert "uploads_data:/app/data/uploads" in backend
    assert not re.search(r"(?m)^\s+-\s+\./", backend)
    assert "healthcheck:" in backend
    assert "/api/v1/health" in backend
    assert "@postgres:5432/" in backend

    assert "pg_isready" in postgres
    assert "$$POSTGRES_USER" in postgres
    assert "$$POSTGRES_DB" in postgres
    assert "postgres_data:/var/lib/postgresql/data" in postgres
    assert "healthcheck:" in postgres
    assert "restart: unless-stopped" in postgres

    assert re.search(r"(?m)^volumes:\s*\n\s+postgres_data:\s*$", text) is not None
    assert re.search(r"(?m)^\s+uploads_data:\s*$", text) is not None


def test_compose_frontend_waits_for_healthy_backend_and_uses_api_upstream() -> None:
    text = _read_compose()
    frontend = _service_block(text, "frontend")

    assert "depends_on:\n      backend:\n        condition: service_healthy" in frontend
    assert re.search(r"(?m)^\s+depends_on:\s*\n\s+-\s+backend\s*$", frontend) is None
    assert "healthcheck:" in frontend
    assert "restart: unless-stopped" in frontend
    assert "API_UPSTREAM: http://backend:8000" in frontend
    assert "npm run dev" not in frontend
    assert "next dev" not in frontend
    assert "--reload" not in frontend
    assert not re.search(r"(?m)^\s+-\s+\./", frontend)
    assert "args:" in frontend
    assert re.search(r"API_UPSTREAM:\s*http://backend:8000", frontend) is not None
