import asyncio
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import settings
from app.models.candidate_profile import CandidateProfile, OnboardingStatus
from app.models.job import Job
from app.models.resume import Resume
from app.services.resume import ResumeUploadInput, upload_resume


async def _chunks(content: bytes):
    yield content


def test_upload_flushes_resume_before_creating_fk_job(
    monkeypatch, tmp_path
) -> None:
    user_id = uuid4()
    profile = CandidateProfile(
        id=uuid4(),
        user_id=user_id,
        display_name="Candidate",
        onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
    )
    session = Mock()
    session.execute.side_effect = (
        SimpleNamespace(scalar_one_or_none=lambda: profile),
        SimpleNamespace(),
    )
    calls: list[str] = []
    added: list[object] = []

    def add(value: object) -> None:
        added.append(value)
        calls.append("resume" if isinstance(value, Resume) else "job")

    session.add.side_effect = add
    session.flush.side_effect = lambda: calls.append("flush")
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))

    result = asyncio.run(
        upload_resume(
            session,
            user_id,
            ResumeUploadInput(
                filename="resume.pdf",
                content_type="application/pdf",
                chunks=_chunks(b"%PDF-1.4\n%%EOF\n"),
            ),
        )
    )

    assert isinstance(added[0], Resume)
    assert isinstance(added[1], Job)
    assert calls == ["resume", "flush", "job"]
    assert added[1].resume_id == result.resume.id
    session.commit.assert_called_once()


def test_upload_rolls_back_and_removes_stored_file_on_database_error(monkeypatch, tmp_path) -> None:
    user_id = uuid4()
    profile = CandidateProfile(
        id=uuid4(),
        user_id=user_id,
        display_name="Candidate",
        onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
    )
    session = Mock()
    session.execute.side_effect = (
        SimpleNamespace(scalar_one_or_none=lambda: profile),
        SimpleNamespace(),
    )
    session.flush.side_effect = SQLAlchemyError("flush failure")
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))

    with pytest.raises(SQLAlchemyError, match="flush failure"):
        asyncio.run(
            upload_resume(
                session,
                user_id,
                ResumeUploadInput(
                    filename="resume.pdf",
                    content_type="application/pdf",
                    chunks=_chunks(b"%PDF-1.4\n%%EOF\n"),
                ),
            )
        )
    session.rollback.assert_called_once()
    assert list(tmp_path.iterdir()) == []
