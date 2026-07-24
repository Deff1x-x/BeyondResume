"""Static deployment contract for docker-compose.yml without a YAML parser."""

from __future__ import annotations

import re
from pathlib import Path

_COMPOSE = Path(__file__).resolve().parents[2] / "docker-compose.yml"
_SERVICE_HEADER = re.compile(r"^  [A-Za-z0-9_-]+:\s*$", re.MULTILINE)
_TOP_LEVEL = re.compile(r"^[A-Za-z0-9_-]+:\s*$", re.MULTILINE)


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


def test_compose_backend_waits_for_healthy_postgres_with_persistent_volume() -> None:
    # Normalize CRLF from Windows checkout so assertions stay portable.
    text = _COMPOSE.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    backend = _service_block(text, "backend")
    postgres = _service_block(text, "postgres")

    assert "depends_on:\n      postgres:\n        condition: service_healthy" in backend
    assert re.search(r"(?m)^\s+depends_on:\s*\n\s+-\s+postgres\s*$", backend) is None
    assert "--reload" not in backend

    assert "pg_isready" in postgres
    assert "$$POSTGRES_USER" in postgres
    assert "$$POSTGRES_DB" in postgres
    assert "postgres_data:/var/lib/postgresql/data" in postgres

    assert re.search(r"(?m)^volumes:\s*\n\s+postgres_data:\s*$", text) is not None
