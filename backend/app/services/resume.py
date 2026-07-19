from contextlib import suppress
from collections.abc import AsyncIterable
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from zipfile import BadZipFile, ZipFile
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.candidate_profile import CandidateProfile
from app.models.resume import Resume
from app.models.job import Job
from app.models.job import JobStatus, JobType

MAX_RESUME_BYTES = 8 * 1024 * 1024
CHUNK_SIZE = 64 * 1024
ALLOWED_RESUME_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


class CandidateProfileRequiredError(Exception):
    pass


class UnsupportedResumeTypeError(Exception):
    pass


class ResumeFileTooLargeError(Exception):
    pass


class EmptyResumeFileError(Exception):
    pass


class MissingResumeFilenameError(Exception):
    pass


class ResumeFilenameTooLongError(Exception):
    pass


class ResumeStorageError(Exception):
    pass


class InvalidResumeContentError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class ResumeUploadInput:
    filename: str | None
    content_type: str | None
    chunks: AsyncIterable[bytes]


@dataclass(frozen=True, slots=True)
class ResumeUploadResult:
    resume: Resume
    job: Job


def get_candidate_profile(session: Session, user_id: UUID) -> CandidateProfile | None:
    return session.execute(
        select(CandidateProfile).where(CandidateProfile.user_id == user_id)
    ).scalar_one_or_none()


def get_current_resume(session: Session, user_id: UUID) -> Resume | None:
    profile = get_candidate_profile(session, user_id)
    if profile is None:
        return None
    return session.execute(
        select(Resume).where(Resume.candidate_id == profile.id, Resume.is_current.is_(True))
    ).scalar_one_or_none()


def get_candidate_resume(session: Session, user_id: UUID, resume_id: UUID) -> Resume | None:
    return session.execute(
        select(Resume)
        .join(CandidateProfile, Resume.candidate_id == CandidateProfile.id)
        .where(Resume.id == resume_id, CandidateProfile.user_id == user_id)
    ).scalar_one_or_none()


def _basename(filename: str | None) -> str:
    if filename is None:
        raise MissingResumeFilenameError
    basename = Path(filename.replace("\\", "/")).name
    if not basename:
        raise MissingResumeFilenameError
    if len(basename) > 255:
        raise ResumeFilenameTooLongError
    return basename


def _extension_for(filename: str, mime_type: str | None) -> str:
    extension = Path(filename).suffix.lower()
    if ALLOWED_RESUME_TYPES.get(extension) != mime_type:
        raise UnsupportedResumeTypeError
    return extension


def _remove_file(path: Path) -> None:
    with suppress(OSError):
        path.unlink()


def _validate_content(extension: str, content: bytes) -> None:
    if extension == ".pdf" and not content.startswith(b"%PDF-"):
        raise InvalidResumeContentError
    if extension == ".docx":
        try:
            with ZipFile(BytesIO(content)) as archive:
                names = set(archive.namelist())
        except BadZipFile as error:
            raise InvalidResumeContentError from error
        if not {"[Content_Types].xml", "word/document.xml"} <= names:
            raise InvalidResumeContentError


async def upload_resume(
    session: Session, user_id: UUID, upload: ResumeUploadInput
) -> ResumeUploadResult:
    profile = get_candidate_profile(session, user_id)
    if profile is None:
        raise CandidateProfileRequiredError

    original_filename = _basename(upload.filename)
    extension = _extension_for(original_filename, upload.content_type)
    upload_dir = Path(settings.upload_dir)
    content = bytearray()
    async for chunk in upload.chunks:
        content.extend(chunk)
        if len(content) > MAX_RESUME_BYTES:
            raise ResumeFileTooLargeError
    if not content:
        raise EmptyResumeFileError
    _validate_content(extension, bytes(content))
    destination = upload_dir / f"{uuid4()}{extension}"
    checksum = sha256(content)

    try:
        upload_dir.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as destination_file:
            destination_file.write(content)
    except ResumeFileTooLargeError:
        _remove_file(destination)
        raise
    except OSError as error:
        _remove_file(destination)
        raise ResumeStorageError from error

    resume = Resume(
        id=uuid4(),
        candidate_id=profile.id,
        original_filename=original_filename,
        stored_path=str(destination),
        mime_type=upload.content_type,
        file_size_bytes=len(content),
        checksum=checksum.hexdigest(),
        extracted_text=None,
        parse_status="uploaded",
    )
    try:
        session.execute(
            update(Resume)
            .where(Resume.candidate_id == profile.id, Resume.is_current.is_(True))
            .values(is_current=False)
        )
        session.add(resume)
        job = Job(resume_id=resume.id, job_type=JobType.RESUME_PARSE, status=JobStatus.PENDING)
        session.add(job)
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        _remove_file(destination)
        raise
    session.refresh(resume)
    return ResumeUploadResult(resume=resume, job=job)


def get_download_path(resume: Resume) -> Path:
    root = Path(settings.upload_dir).resolve()
    path = Path(resume.stored_path).resolve()
    if root not in path.parents or not path.is_file():
        raise ResumeStorageError
    return path
