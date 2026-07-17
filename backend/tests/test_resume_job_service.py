from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.models.job import Job, JobStatus, JobType
from app.models.resume import Resume
from app.services.resume_jobs import (
    JobTransitionError,
    ResumeTransitionError,
    claim_job,
    complete_job,
    fail_job,
    is_retry_available,
    request_resume_parse,
    retry_failed_resume,
)


def make_resume(status: str = "uploaded") -> Resume:
    return Resume(
        id=uuid4(),
        candidate_id=uuid4(),
        original_filename="resume.pdf",
        stored_path="safe.pdf",
        mime_type="application/pdf",
        file_size_bytes=1,
        parse_status=status,
    )


def make_job(resume: Resume, status: JobStatus = JobStatus.PENDING) -> Job:
    return Job(
        id=uuid4(),
        resume_id=resume.id,
        job_type=JobType.RESUME_PARSE,
        status=status,
        created_at=datetime.now(UTC),
    )


def test_claim_moves_pending_job_to_running_once() -> None:
    resume = make_resume()
    job = make_job(resume)
    session = Mock()
    session.execute.side_effect = [
        SimpleNamespace(rowcount=1),
        SimpleNamespace(scalar_one_or_none=lambda: job),
    ]

    claimed = claim_job(session, job.id)

    assert claimed is job
    assert session.commit.called


def test_claim_rejects_job_that_is_not_pending() -> None:
    session = Mock()
    session.execute.return_value = SimpleNamespace(rowcount=0)

    with pytest.raises(JobTransitionError):
        claim_job(session, uuid4())

    session.rollback.assert_called_once()


def test_complete_marks_job_and_uploaded_resume_as_complete() -> None:
    resume = make_resume()
    job = make_job(resume, JobStatus.RUNNING)
    session = Mock()
    session.execute.return_value = SimpleNamespace(scalar_one=lambda: resume)

    complete_job(session, job)

    assert job.status == JobStatus.COMPLETED
    assert job.completed_at is not None
    assert resume.parse_status == "parsed"
    assert resume.parsed_at is not None
    assert resume.failed_at is None
    assert resume.parse_error_code is None


def test_fail_marks_job_and_uploaded_resume_with_safe_error() -> None:
    resume = make_resume()
    job = make_job(resume, JobStatus.RUNNING)
    session = Mock()
    session.execute.return_value = SimpleNamespace(scalar_one=lambda: resume)

    fail_job(session, job, "RESUME_FILE_MISSING", "Resume file is unavailable")

    assert job.status == JobStatus.FAILED
    assert job.failed_at is not None
    assert job.error_code == "RESUME_FILE_MISSING"
    assert resume.parse_status == "failed"
    assert resume.failed_at is not None
    assert resume.parsed_at is None
    assert resume.parse_error_message == "Resume file is unavailable"


@pytest.mark.parametrize("job_status", [JobStatus.PENDING, JobStatus.COMPLETED, JobStatus.FAILED])
def test_terminal_or_pending_job_cannot_complete(job_status: JobStatus) -> None:
    resume = make_resume()
    job = make_job(resume, job_status)

    with pytest.raises(JobTransitionError):
        complete_job(Mock(), job)


def test_resume_transition_is_rejected_after_it_has_failed() -> None:
    resume = make_resume("failed")
    job = make_job(resume, JobStatus.RUNNING)
    session = Mock()
    session.execute.return_value = SimpleNamespace(scalar_one=lambda: resume)

    with pytest.raises(ResumeTransitionError):
        complete_job(session, job)


def test_retry_creates_one_new_pending_job_for_failed_resume() -> None:
    resume = make_resume("failed")
    session = Mock()
    session.execute.return_value = SimpleNamespace(scalar_one_or_none=lambda: None)

    job = retry_failed_resume(session, resume)

    assert job.status == JobStatus.PENDING
    assert job.resume_id == resume.id
    assert resume.parse_status == "uploaded"
    session.add.assert_called_once_with(job)
    session.commit.assert_called_once()


def test_retry_rejects_non_failed_resume() -> None:
    with pytest.raises(ResumeTransitionError):
        retry_failed_resume(Mock(), make_resume())


def test_failed_resume_retry_claim_and_complete_clears_previous_error() -> None:
    resume = make_resume("failed")
    resume.failed_at = datetime.now(UTC)
    resume.parse_error_code = "OLD_ERROR"
    resume.parse_error_message = "Old error"
    retry_session = Mock()
    retry_session.execute.return_value = SimpleNamespace(scalar_one_or_none=lambda: None)

    job = retry_failed_resume(retry_session, resume)
    assert resume.parse_status == "uploaded"
    job.status = JobStatus.RUNNING  # State after the atomic claim and re-read.
    complete_session = Mock()
    complete_session.execute.return_value = SimpleNamespace(scalar_one=lambda: resume)

    complete_job(complete_session, job)

    assert job.status == JobStatus.COMPLETED
    assert resume.parse_status == "parsed"
    assert resume.failed_at is None
    assert resume.parse_error_code is None
    assert resume.parse_error_message is None
    assert resume.parsed_at is not None


def test_failed_resume_retry_claim_and_fail_replaces_previous_error() -> None:
    resume = make_resume("failed")
    old_failed_at = datetime.now(UTC)
    resume.failed_at = old_failed_at
    resume.parse_error_code = "OLD_ERROR"
    resume.parse_error_message = "Old error"
    retry_session = Mock()
    retry_session.execute.return_value = SimpleNamespace(scalar_one_or_none=lambda: None)

    job = retry_failed_resume(retry_session, resume)
    job.status = JobStatus.RUNNING  # State after the atomic claim and re-read.
    fail_session = Mock()
    fail_session.execute.return_value = SimpleNamespace(scalar_one=lambda: resume)

    fail_job(fail_session, job, "NEW_ERROR", "New safe error")

    assert job.status == JobStatus.FAILED
    assert resume.parse_status == "failed"
    assert resume.parse_error_code == "NEW_ERROR"
    assert resume.parse_error_message == "New safe error"
    assert resume.failed_at is not None
    assert resume.failed_at >= old_failed_at
    assert job.failed_at == resume.failed_at


def test_retry_with_active_parse_job_does_not_change_failed_resume() -> None:
    resume = make_resume("failed")
    resume.parse_error_code = "OLD_ERROR"
    active = make_job(resume, JobStatus.PENDING)
    session = Mock()
    session.execute.return_value = SimpleNamespace(scalar_one_or_none=lambda: active)

    returned = retry_failed_resume(session, resume)

    assert returned is active
    assert resume.parse_status == "failed"
    assert resume.parse_error_code == "OLD_ERROR"
    session.add.assert_not_called()
    session.commit.assert_not_called()


@pytest.mark.parametrize("operation", [complete_job, fail_job])
def test_completion_or_failure_commit_error_rolls_back_both_models(operation: object) -> None:
    resume = make_resume()
    job = make_job(resume, JobStatus.RUNNING)
    session = Mock()
    session.execute.return_value = SimpleNamespace(scalar_one=lambda: resume)
    session.commit.side_effect = SQLAlchemyError("commit failed")

    with pytest.raises(SQLAlchemyError):
        if operation is complete_job:
            complete_job(session, job)
        else:
            fail_job(session, job, "SAFE_ERROR", "Safe error")

    session.rollback.assert_called_once()


@pytest.mark.parametrize("status", ["uploaded", "parsed"])
def test_retry_availability_is_false_for_non_failed_resume(status: str) -> None:
    resume = make_resume(status)
    job = make_job(resume, JobStatus.FAILED)

    assert is_retry_available(Mock(), job, resume) is False


@pytest.mark.parametrize("active_status", [JobStatus.PENDING, JobStatus.RUNNING])
def test_retry_availability_is_false_with_active_resume_parse_job(active_status: JobStatus) -> None:
    resume = make_resume("failed")
    job = make_job(resume, JobStatus.FAILED)
    active = make_job(resume, active_status)
    session = Mock()
    session.execute.return_value = SimpleNamespace(scalar_one_or_none=lambda: active.id)

    assert is_retry_available(session, job, resume) is False


def test_retry_availability_is_true_only_for_failed_resume_parse_job_without_active_job() -> None:
    resume = make_resume("failed")
    job = make_job(resume, JobStatus.FAILED)
    session = Mock()
    session.execute.return_value = SimpleNamespace(scalar_one_or_none=lambda: None)

    assert is_retry_available(session, job, resume) is True


def test_non_resume_parse_job_cannot_make_resume_retry_available() -> None:
    resume = make_resume("failed")
    job = make_job(resume, JobStatus.FAILED)
    job.job_type = JobType.PROFILE_ANALYSIS

    assert is_retry_available(Mock(), job, resume) is False


@pytest.mark.parametrize("job_status", [JobStatus.PENDING, JobStatus.RUNNING, JobStatus.COMPLETED])
def test_non_failed_job_cannot_make_retry_available(job_status: JobStatus) -> None:
    resume = make_resume("failed")
    job = make_job(resume, job_status)

    assert is_retry_available(Mock(), job, resume) is False


def test_parse_request_returns_existing_active_job_idempotently() -> None:
    resume = make_resume()
    active = make_job(resume, JobStatus.PENDING)
    session = Mock()
    session.execute.return_value = SimpleNamespace(scalar_one_or_none=lambda: active)

    assert request_resume_parse(session, resume) is active
    session.add.assert_not_called()
    session.commit.assert_not_called()


def test_parse_request_creates_pending_job_for_uploaded_resume() -> None:
    resume = make_resume()
    session = Mock()
    session.execute.return_value = SimpleNamespace(scalar_one_or_none=lambda: None)

    job = request_resume_parse(session, resume)

    assert job.job_type == JobType.RESUME_PARSE
    assert job.status == JobStatus.PENDING
    assert job.resume_id == resume.id
    session.add.assert_called_once_with(job)
    session.commit.assert_called_once()


def test_parse_request_reuses_retry_lifecycle_for_failed_resume() -> None:
    resume = make_resume("failed")
    session = Mock()
    session.execute.return_value = SimpleNamespace(scalar_one_or_none=lambda: None)

    job = request_resume_parse(session, resume)

    assert job.status == JobStatus.PENDING
    assert resume.parse_status == "uploaded"
