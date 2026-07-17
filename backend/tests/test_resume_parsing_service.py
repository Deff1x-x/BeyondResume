import asyncio
import time
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.models.resume import Resume
from app.services.resume_parsing import (
    ResumeAlreadyProcessedError,
    ResumeNotFoundError,
    ResumeParsingFailedError,
    ResumeParseTimeoutError,
    parse_resume,
)
from app.utils.resume_parse import ResumeFileReadError


def make_resume(status: str = "uploaded") -> Resume:
    return Resume(
        id=uuid4(),
        candidate_id=uuid4(),
        original_filename="resume.pdf",
        stored_path="/uploads/resume.pdf",
        mime_type="application/pdf",
        file_size_bytes=1,
        parse_status=status,
    )


def make_session(resume: Resume | None) -> Mock:
    session = Mock()
    session.execute.return_value.scalar_one_or_none.return_value = resume
    return session


def test_parse_uploaded_resume_updates_text(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services import resume_parsing

    resume = make_resume()
    session = make_session(resume)
    monkeypatch.setattr(resume_parsing, "extract_resume_text", lambda *_args: "Python\nFastAPI")

    result = asyncio.run(parse_resume(session, resume.id))

    assert result.parse_status == "parsed"
    assert result.extracted_text == "Python\nFastAPI"
    session.commit.assert_called_once()


def test_parse_failure_persists_failed_state(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services import resume_parsing

    resume = make_resume()
    session = make_session(resume)
    monkeypatch.setattr(
        resume_parsing,
        "extract_resume_text",
        lambda *_args: (_ for _ in ()).throw(ResumeFileReadError),
    )

    with pytest.raises(ResumeParsingFailedError):
        asyncio.run(parse_resume(session, resume.id))

    assert resume.parse_status == "failed"
    assert resume.extracted_text is None
    session.commit.assert_called_once()


def test_missing_and_processed_resumes_do_not_commit() -> None:
    with pytest.raises(ResumeNotFoundError):
        asyncio.run(parse_resume(make_session(None), uuid4()))

    session = make_session(make_resume("parsed"))
    with pytest.raises(ResumeAlreadyProcessedError):
        asyncio.run(parse_resume(session, uuid4()))
    session.commit.assert_not_called()


def test_database_error_rolls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services import resume_parsing

    resume = make_resume()
    session = make_session(resume)
    session.commit.side_effect = SQLAlchemyError("database error")
    monkeypatch.setattr(resume_parsing, "extract_resume_text", lambda *_args: "text")

    with pytest.raises(SQLAlchemyError):
        asyncio.run(parse_resume(session, resume.id))
    session.rollback.assert_called_once()


def test_parser_failure_commit_error_prioritizes_database_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services import resume_parsing

    resume = make_resume()
    session = make_session(resume)
    session.commit.side_effect = SQLAlchemyError("database error")
    monkeypatch.setattr(
        resume_parsing,
        "extract_resume_text",
        lambda *_args: (_ for _ in ()).throw(ResumeFileReadError),
    )

    with pytest.raises(SQLAlchemyError):
        asyncio.run(parse_resume(session, resume.id))
    session.rollback.assert_called_once()


def test_timeout_marks_resume_failed_and_commits(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.config import settings
    from app.services import resume_parsing

    resume = make_resume()
    session = make_session(resume)
    monkeypatch.setattr(settings, "resume_parse_timeout_seconds", 0.01)
    monkeypatch.setattr(resume_parsing, "extract_resume_text", lambda *_args: time.sleep(0.1))

    with pytest.raises(ResumeParseTimeoutError):
        asyncio.run(parse_resume(session, resume.id))
    assert resume.parse_status == "failed"
    session.commit.assert_called_once()


def test_parser_uses_resume_mime_type_not_filename_extension(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services import resume_parsing

    resume = make_resume()
    resume.stored_path = "/uploads/resume.docx"
    resume.mime_type = "application/pdf"
    session = make_session(resume)
    captured: list[str] = []

    def extract(_path, mime_type: str) -> str:
        captured.append(mime_type)
        return "PDF text"

    monkeypatch.setattr(resume_parsing, "extract_resume_text", extract)
    asyncio.run(parse_resume(session, resume.id))

    assert captured == ["application/pdf"]
