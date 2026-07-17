import asyncio
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.models.job import Job, JobStatus, JobType
from app.models.resume import Resume
from app.services.resume_parsing import run_resume_parse_job, run_resume_parse_job_task
from app.utils.resume_parse import ResumeFileReadError


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


def make_running_job(resume: Resume) -> Job:
    return Job(
        id=uuid4(),
        resume_id=resume.id,
        job_type=JobType.RESUME_PARSE,
        status=JobStatus.RUNNING,
        created_at=datetime.now(UTC),
        started_at=datetime.now(UTC),
    )


def test_worker_saves_plain_text_and_completes_job(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services import resume_parsing

    resume = make_resume()
    job = make_running_job(resume)
    session = Mock()
    monkeypatch.setattr(resume_parsing, "claim_job", lambda *_args: job)
    monkeypatch.setattr(resume_parsing, "get_resume", lambda *_args: resume)
    monkeypatch.setattr(resume_parsing, "get_download_path", lambda *_args: Path("safe.pdf"))

    async def extract(_: Resume, **_kwargs: object) -> str:
        return "Python\nFastAPI"

    def complete(_: Mock, received_job: Job) -> Job:
        assert received_job is job
        assert resume.extracted_text == "Python\nFastAPI"
        resume.parse_status = "parsed"
        job.status = JobStatus.COMPLETED
        return job

    monkeypatch.setattr(resume_parsing, "extract_plain_text", extract)
    monkeypatch.setattr(resume_parsing, "complete_job", complete)

    result = asyncio.run(run_resume_parse_job(session, job.id))

    assert result.status == JobStatus.COMPLETED
    assert resume.parse_status == "parsed"
    assert resume.extracted_text == "Python\nFastAPI"


def test_worker_marks_resume_and_job_failed_on_parser_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services import resume_parsing

    resume = make_resume()
    job = make_running_job(resume)
    session = Mock()
    monkeypatch.setattr(resume_parsing, "claim_job", lambda *_args: job)
    monkeypatch.setattr(resume_parsing, "get_resume", lambda *_args: resume)
    monkeypatch.setattr(resume_parsing, "get_download_path", lambda *_args: Path("safe.pdf"))

    async def extract(_: Resume, **_kwargs: object) -> str:
        raise ResumeFileReadError

    def fail(_: Mock, received_job: Job, code: str, message: str) -> Job:
        assert received_job is job
        assert code == "INTERNAL_ERROR"
        assert message == "Resume processing failed"
        assert resume.extracted_text is None
        resume.parse_status = "failed"
        job.status = JobStatus.FAILED
        return job

    monkeypatch.setattr(resume_parsing, "extract_plain_text", extract)
    monkeypatch.setattr(resume_parsing, "fail_job", fail)

    result = asyncio.run(run_resume_parse_job(session, job.id))

    assert result.status == JobStatus.FAILED
    assert resume.parse_status == "failed"


def test_worker_rejects_non_resume_parse_job(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services import resume_parsing
    from app.services.resume_jobs import JobTransitionError

    resume = make_resume()
    job = make_running_job(resume)
    job.job_type = JobType.PROFILE_ANALYSIS
    monkeypatch.setattr(resume_parsing, "claim_job", lambda *_args: job)

    with pytest.raises(JobTransitionError):
        asyncio.run(run_resume_parse_job(Mock(), job.id))


def test_background_task_owns_and_closes_its_session(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services import resume_parsing

    session = Mock()
    job_id = uuid4()
    monkeypatch.setattr(resume_parsing, "SessionLocal", lambda: session)
    called: list[tuple[Mock, object]] = []

    async def run(received_session: Mock, received_job_id: object) -> Job:
        called.append((received_session, received_job_id))
        return Mock(spec=Job)

    monkeypatch.setattr(resume_parsing, "run_resume_parse_job", run)

    asyncio.run(run_resume_parse_job_task(job_id))

    assert called == [(session, job_id)]
    session.close.assert_called_once()
