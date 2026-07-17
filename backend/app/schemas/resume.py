from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.job import JobStatus


class ResumeUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_filename: str
    mime_type: str
    file_size_bytes: int
    parse_status: Literal["uploaded"]
    created_at: datetime


class ResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_filename: str
    mime_type: str
    file_size: int
    status: Literal["uploaded", "parsed", "failed"]
    uploaded_at: datetime


class JobPollingResponse(BaseModel):
    """Safe status projection for a resume-processing job."""

    id: UUID
    status: JobStatus
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    failed_at: datetime | None
    error_code: str | None
    error_message: str | None
    resume_status: Literal["uploaded", "parsed", "failed"]
    retry_available: bool
