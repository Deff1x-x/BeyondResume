from contextlib import suppress
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.candidate_profile import CandidateProfile
from app.models.resume import Resume

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


def get_candidate_profile(session: Session, user_id: UUID) -> CandidateProfile | None:
    return session.execute(
        select(CandidateProfile).where(CandidateProfile.user_id == user_id)
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


async def upload_resume(session: Session, user_id: UUID, upload_file: UploadFile) -> Resume:
    operation_error: BaseException | None = None
    try:
        return await _upload_resume(session, user_id, upload_file)
    except BaseException as error:
        operation_error = error
        raise
    finally:
        try:
            await upload_file.close()
        except Exception:
            if operation_error is None:
                raise


async def _upload_resume(session: Session, user_id: UUID, upload_file: UploadFile) -> Resume:
    profile = get_candidate_profile(session, user_id)
    if profile is None:
        raise CandidateProfileRequiredError

    original_filename = _basename(upload_file.filename)
    extension = _extension_for(original_filename, upload_file.content_type)
    upload_dir = Path(settings.upload_dir)
    destination = upload_dir / f"{uuid4()}{extension}"

    try:
        upload_dir.mkdir(parents=True, exist_ok=True)
        size = 0
        with destination.open("xb") as destination_file:
            while chunk := await upload_file.read(CHUNK_SIZE):
                size += len(chunk)
                if size > MAX_RESUME_BYTES:
                    raise ResumeFileTooLargeError
                destination_file.write(chunk)
    except ResumeFileTooLargeError:
        _remove_file(destination)
        raise
    except OSError as error:
        _remove_file(destination)
        raise ResumeStorageError from error

    if size == 0:
        _remove_file(destination)
        raise EmptyResumeFileError

    resume = Resume(
        candidate_id=profile.id,
        original_filename=original_filename,
        stored_path=str(destination),
        mime_type=upload_file.content_type,
        file_size_bytes=size,
        extracted_text=None,
        parse_status="uploaded",
    )
    session.add(resume)
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        _remove_file(destination)
        raise
    session.refresh(resume)
    return resume
