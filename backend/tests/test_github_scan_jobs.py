from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.integrations.github import GitHubRateLimitError
from app.models.job import JobStatus, JobType
from app.services.github_scan_jobs import _failure_details, run_github_scan_job


def test_rate_limit_failure_is_recorded_with_a_specific_code() -> None:
    assert _failure_details(GitHubRateLimitError()) == (
        "GITHUB_RATE_LIMIT",
        "GitHub repository data could not be fetched",
    )


def test_scan_job_logs_traceback_and_fails_on_rate_limit(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    job_id = uuid4()
    job = SimpleNamespace(
        job_type=JobType.GITHUB_SCAN,
        candidate_id=uuid4(),
        subject_id=uuid4(),
        status=JobStatus.RUNNING,
    )
    session = Mock()
    failed_job = SimpleNamespace(status=JobStatus.FAILED, error_code="GITHUB_RATE_LIMIT")
    fail = Mock(return_value=failed_job)
    monkeypatch.setattr("app.services.github_scan_jobs.claim_job", Mock(return_value=job))
    monkeypatch.setattr(
        "app.services.github_scan_jobs.run_github_repository_scan",
        Mock(side_effect=GitHubRateLimitError("GitHub rate limit is exhausted")),
    )
    monkeypatch.setattr("app.services.github_scan_jobs.fail_running_job", fail)

    with caplog.at_level("ERROR", logger="app.services.github_scan_jobs"):
        result = run_github_scan_job(session, job_id)

    assert result is failed_job
    session.rollback.assert_called_once()
    assert fail.call_args.args[2:] == (
        "GITHUB_RATE_LIMIT",
        "GitHub repository data could not be fetched",
    )
    assert caplog.records[-1].exc_info is not None
