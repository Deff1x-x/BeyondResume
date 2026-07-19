import asyncio
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.job import Job, JobType
from app.models.resume import Resume
from app.services.resume import ResumeStorageError, get_download_path
from app.services.resume_evidence import generate_resume_evidence
from app.services.resume_jobs import (
    JobTransitionError,
    claim_job,
    complete_job,
    fail_job,
)
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
        text = await extract_plain_text(resume)
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


async def extract_plain_text(resume: Resume, *, safe_path: Path | None = None) -> str:
    """Use the established parser with its timeout and no public result surface."""
    path = safe_path if safe_path is not None else Path(resume.stored_path)
    return await asyncio.wait_for(
        asyncio.to_thread(extract_resume_text, path, resume.mime_type),
        timeout=settings.resume_parse_timeout_seconds,
    )


def _failure_details(error: BaseException) -> tuple[str, str]:
    if isinstance(error, UnsupportedResumeParserTypeError):
        return "UNSUPPORTED_FORMAT", "Resume format is not supported"
    if isinstance(error, ResumeDocumentParseError):
        return "CORRUPTED_FILE", "Resume file could not be processed"
    if isinstance(error, EmptyExtractedResumeTextError):
        return "EMPTY_TEXT", "Resume does not contain readable text"
    if isinstance(error, asyncio.TimeoutError):
        return "EXTRACTOR_TIMEOUT", "Resume processing timed out"
    return "INTERNAL_ERROR", "Resume processing failed"


async def run_resume_parse_job(session: Session, job_id: UUID) -> Job:
    """Run one pending resume_parse Job using the existing Job state machine."""
    job = claim_job(session, job_id)
    if job.job_type != JobType.RESUME_PARSE or job.resume_id is None:
        raise JobTransitionError("Job is not a resume parse job")

    resume = get_resume(session, job.resume_id)
    if resume is None:
        raise ResumeNotFoundError
    if resume.parse_status != "uploaded":
        raise ResumeAlreadyProcessedError

    try:
        text = await extract_plain_text(resume, safe_path=get_download_path(resume))
    except (
        asyncio.TimeoutError,
        ResumeStorageError,
        UnsupportedResumeParserTypeError,
        ResumeFileReadError,
        ResumeDocumentParseError,
        EmptyExtractedResumeTextError,
    ) as error:
        resume.extracted_text = None
        code, message = _failure_details(error)
        return fail_job(session, job, code, message)

    resume.extracted_text = text
    try:
        # Attach the parsed resume to the shared Evidence pipeline (no AI / skills yet).
        generate_resume_evidence(session, resume)
    except (ValueError, SQLAlchemyError):
        resume.extracted_text = None
        return fail_job(session, job, "INTERNAL_ERROR", "Resume processing failed")
    return complete_job(session, job)


async def run_resume_parse_job_task(job_id: UUID) -> None:
    """Run a background parse using a session owned by the background task."""
    session = SessionLocal()
    try:
        await run_resume_parse_job(session, job_id)
    finally:
        session.close()
