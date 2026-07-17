import asyncio
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.resume import Resume
from app.utils.resume_parse import (
    EmptyExtractedResumeTextError,
    ResumeDocumentParseError,
    ResumeFileReadError,
    UnsupportedResumeParserTypeError,
    extract_resume_text,
)


class ResumeNotFoundError(Exception):
    pass


class ResumeAlreadyProcessedError(Exception):
    pass


class ResumeParseTimeoutError(Exception):
    pass


class ResumeParsingFailedError(Exception):
    pass


def get_resume(session: Session, resume_id: UUID) -> Resume | None:
    return session.execute(select(Resume).where(Resume.id == resume_id)).scalar_one_or_none()


def _commit_failed(session: Session, resume: Resume) -> None:
    resume.extracted_text = None
    resume.parse_status = "failed"
    try:
        session.commit()
        session.refresh(resume)
    except SQLAlchemyError:
        session.rollback()
        raise


async def parse_resume(session: Session, resume_id: UUID) -> Resume:
    resume = get_resume(session, resume_id)
    if resume is None:
        raise ResumeNotFoundError
    if resume.parse_status != "uploaded":
        raise ResumeAlreadyProcessedError

    try:
        text = await asyncio.wait_for(
            asyncio.to_thread(extract_resume_text, Path(resume.stored_path), resume.mime_type),
            timeout=settings.resume_parse_timeout_seconds,
        )
    except asyncio.TimeoutError as error:
        _commit_failed(session, resume)
        raise ResumeParseTimeoutError from error
    except (
        UnsupportedResumeParserTypeError,
        ResumeFileReadError,
        ResumeDocumentParseError,
        EmptyExtractedResumeTextError,
    ) as error:
        _commit_failed(session, resume)
        raise ResumeParsingFailedError from error

    resume.extracted_text = text
    resume.parse_status = "parsed"
    try:
        session.commit()
        session.refresh(resume)
    except SQLAlchemyError:
        session.rollback()
        raise
    return resume
