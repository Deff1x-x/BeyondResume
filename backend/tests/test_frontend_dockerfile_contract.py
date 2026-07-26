"""Static deployment contract for the frontend production Docker image."""

from __future__ import annotations

from pathlib import Path

_FRONTEND_ROOT = Path(__file__).resolve().parents[2] / "frontend"
_DOCKERFILE = _FRONTEND_ROOT / "Dockerfile"
_DOCKERIGNORE = _FRONTEND_ROOT / ".dockerignore"
_NEXT_CONFIG = _FRONTEND_ROOT / "next.config.mjs"


def _normalize(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def test_frontend_dockerfile_is_production_multi_stage() -> None:
    text = _normalize(_DOCKERFILE.read_text(encoding="utf-8"))

    assert "node:22-alpine" in text
    assert text.count("FROM ") >= 3
    assert "npm ci" in text
    assert "npm run build" in text
    assert "npm run dev" not in text
    assert "next dev" not in text
    assert "npm install" not in text
    assert "NODE_ENV=production" in text or "NODE_ENV=production \\" in text
    assert "NEXT_TELEMETRY_DISABLED=1" in text
    assert "API_UPSTREAM" in text
    assert "http://backend:8000" in text
    assert 'CMD ["node", "server.js"]' in text
    assert "standalone" in text.lower() or ".next/standalone" in text
    assert "USER nextjs" in text


def test_frontend_dockerignore_excludes_local_caches() -> None:
    text = _normalize(_DOCKERIGNORE.read_text(encoding="utf-8"))
    lines = {line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")}

    assert "node_modules" in lines
    assert ".next" in lines
    assert ".env" in lines
    assert "package.json" not in lines
    assert "package-lock.json" not in lines
    assert "next.config.mjs" not in lines
    assert "app" not in lines
    assert "public" not in lines


def test_next_config_enables_standalone_output() -> None:
    text = _normalize(_NEXT_CONFIG.read_text(encoding="utf-8"))
    assert 'output: "standalone"' in text
    assert "API_UPSTREAM" in text
