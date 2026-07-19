import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.models.candidate_profile import CandidateProfile
from app.models.job import Job
from app.services.resume import (
    CandidateProfileRequiredError,
    InvalidResumeContentError,
    ResumeFileTooLargeError,
    ResumeUploadInput,
    upload_resume,
)


class FakeUploadFile:
    def __init__(self, filename: str, content_type: str, content: bytes) -> None:
        self.filename = filename
        self.content_type = content_type
        self._content = content
        self._offset = 0

    async def read(self, size: int) -> bytes:
        chunk = self._content[self._offset : self._offset + size]
        self._offset += len(chunk)
        return chunk


async def upload_chunks(upload_file: FakeUploadFile) -> AsyncIterator[bytes]:
    while chunk := await upload_file.read(64 * 1024):
        yield chunk


def make_upload_input(upload_file: FakeUploadFile) -> ResumeUploadInput:
    return ResumeUploadInput(
        filename=upload_file.filename,
        content_type=upload_file.content_type,
        chunks=upload_chunks(upload_file),
    )


def make_profile() -> CandidateProfile:
    return CandidateProfile(
        id=uuid4(),
        user_id=uuid4(),
        display_name="Alan Yerkin",
        onboarding_status="profile_required",
    )


def make_session(profile: CandidateProfile | None) -> Mock:
    session = Mock()
    session.execute.return_value.scalar_one_or_none.return_value = profile
    return session


def test_upload_streams_file_and_creates_uploaded_resume(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core.config import settings

    profile = make_profile()
    session = make_session(profile)
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    session.refresh.side_effect = lambda resume: setattr(resume, "created_at", datetime.now(UTC))

    upload_file = FakeUploadFile(
        "C:\\Users\\Alan\\Resume.PDF", "application/pdf", b"%PDF-1.4\ncontent"
    )
    upload_result = asyncio.run(
        upload_resume(
            session,
            profile.user_id,
            make_upload_input(upload_file),
        )
    )
    resume = upload_result.resume
    job = upload_result.job

    assert resume.original_filename == "Resume.PDF"
    assert resume.file_size_bytes == len(b"%PDF-1.4\ncontent")
    assert resume.parse_status == "uploaded"
    assert resume.checksum
    assert resume.extracted_text is None
    assert (tmp_path / f"{resume.id}.pdf") != tmp_path / "Resume.PDF"
    assert (tmp_path / resume.stored_path.split("\\")[-1]).exists()
    added = [call.args[0] for call in session.add.call_args_list]
    assert resume in added
    assert any(
        isinstance(item, Job) and item.job_type == "resume_parse" and item.status == "pending"
        for item in added
    )
    assert job.resume_id == resume.id
    session.commit.assert_called_once()


def test_upload_rejects_oversized_file_and_cleans_partial_file(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core.config import settings
    from app.services.resume import MAX_RESUME_BYTES

    profile = make_profile()
    session = make_session(profile)
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))

    upload_file = FakeUploadFile("resume.pdf", "application/pdf", b"x" * (MAX_RESUME_BYTES + 1))
    with pytest.raises(ResumeFileTooLargeError):
        asyncio.run(
            upload_resume(
                session,
                profile.user_id,
                make_upload_input(upload_file),
            )
        )

    assert list(tmp_path.iterdir()) == []
    session.add.assert_not_called()


@pytest.mark.parametrize(
    ("filename", "mime_type", "content"),
    [
        ("resume.pdf", "application/pdf", b"not a PDF"),
        (
            "resume.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            b"not a DOCX archive",
        ),
    ],
)
def test_upload_rejects_malformed_content_before_file_or_database_mutation(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
    filename: str,
    mime_type: str,
    content: bytes,
) -> None:
    from app.core.config import settings

    profile = make_profile()
    session = make_session(profile)
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    upload_file = FakeUploadFile(filename, mime_type, content)

    with pytest.raises(InvalidResumeContentError):
        asyncio.run(upload_resume(session, profile.user_id, make_upload_input(upload_file)))

    session.add.assert_not_called()
    session.commit.assert_not_called()
    assert list(tmp_path.iterdir()) == []


def test_upload_database_failure_rolls_back_and_removes_file(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core.config import settings

    profile = make_profile()
    session = make_session(profile)
    session.commit.side_effect = SQLAlchemyError("database error")
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))

    upload_file = FakeUploadFile("resume.pdf", "application/pdf", b"%PDF-1.4\ncontent")
    with pytest.raises(SQLAlchemyError):
        asyncio.run(
            upload_resume(
                session,
                profile.user_id,
                make_upload_input(upload_file),
            )
        )

    session.rollback.assert_called_once()
    assert list(tmp_path.iterdir()) == []


def test_upload_job_creation_failure_rolls_back_resume_and_removes_file(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core.config import settings

    profile = make_profile()
    session = make_session(profile)
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))

    def add(entity: object) -> None:
        if isinstance(entity, Job):
            raise SQLAlchemyError("job creation error")

    session.add.side_effect = add
    upload_file = FakeUploadFile("resume.pdf", "application/pdf", b"%PDF-1.4\ncontent")

    with pytest.raises(SQLAlchemyError):
        asyncio.run(upload_resume(session, profile.user_id, make_upload_input(upload_file)))

    session.rollback.assert_called_once()
    session.commit.assert_not_called()
    assert list(tmp_path.iterdir()) == []


def test_upload_storage_failure_does_not_persist_resume(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core.config import settings
    from app.services.resume import ResumeStorageError

    profile = make_profile()
    session = make_session(profile)
    upload_dir = tmp_path / "not-a-directory"
    upload_dir.write_text("file", encoding="utf-8")
    monkeypatch.setattr(settings, "upload_dir", str(upload_dir))
    upload_file = FakeUploadFile("resume.pdf", "application/pdf", b"%PDF-1.4\ncontent")

    with pytest.raises(ResumeStorageError):
        asyncio.run(upload_resume(session, profile.user_id, make_upload_input(upload_file)))

    session.add.assert_not_called()


def test_upload_requires_existing_candidate_profile(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core.config import settings

    session = make_session(None)
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))

    with pytest.raises(CandidateProfileRequiredError):
        asyncio.run(
            upload_resume(
                session,
                uuid4(),
                make_upload_input(FakeUploadFile("resume.pdf", "application/pdf", b"content")),
            )
        )

    session.add.assert_not_called()
