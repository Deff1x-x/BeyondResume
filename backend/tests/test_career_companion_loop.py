"""Unit tests for Career Companion evidence verification helpers."""

from uuid import uuid4

from app.services.career_companion.chat import _detect_revision
from app.services.career_companion.plan_service import ALLOWED_MANUAL_STATUSES
from app.services.career_companion_jobs import context_is_large


def test_detect_revision_hints():
    assert _detect_revision("Make the plan shorter please") == "shorter"
    assert _detect_revision("Use only existing projects") == "existing project"
    assert _detect_revision("What is Docker?") is None


def test_context_is_large_thresholds():
    assert context_is_large(project_count=8, vacancy_count=1) is True
    assert context_is_large(project_count=1, vacancy_count=12) is True
    assert context_is_large(project_count=2, vacancy_count=3) is False


def test_verification_completion_logic_is_evidence_gated():
    assert "completed" not in ALLOWED_MANUAL_STATUSES
    assert "evidence_detected" not in ALLOWED_MANUAL_STATUSES


def test_github_scan_refresh_does_not_enqueue_generation(monkeypatch):
    """Regression: evidence refresh must never spawn roadmap_generation jobs."""
    from app.services import career_companion_hooks as hooks

    enqueued = {"count": 0}

    def boom(*_a, **_k):
        enqueued["count"] += 1
        raise AssertionError("refresh must not enqueue generation")

    monkeypatch.setattr(
        "app.services.career_companion_jobs.request_roadmap_generation",
        boom,
        raising=False,
    )
    monkeypatch.setattr(
        "app.services.career_companion.verification.refresh_plan_from_evidence",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr("app.db.session.SessionLocal", lambda: type("S", (), {"rollback": lambda self: None, "close": lambda self: None})())

    hooks.maybe_refresh_companion_after_evidence(object(), uuid4())
    assert enqueued["count"] == 0
