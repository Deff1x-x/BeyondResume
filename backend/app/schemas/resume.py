from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.job import JobStatus, JobType


class ResumeUploadAcceptedResponse(BaseModel):
    resume_id: UUID
    job_id: UUID


class ResumeEvidenceSkillResponse(BaseModel):
    name: str
    category: str
    extraction_method: str
    evidence_confidence: float


class ResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_filename: str
    mime_type: str
    file_size: int
    status: Literal["uploaded", "parsed", "failed"]
    uploaded_at: datetime
    parsed_at: datetime | None = None
    extracted_text_length: int | None = None
    evidence_id: UUID | None = None
    skills: list[ResumeEvidenceSkillResponse] = []


class JobPollingResponse(BaseModel):
    """Safe status projection for any background job.

    resume_status is populated only for resume-bound jobs; other job types
    (for example github_scan) return null.
    """

    id: UUID
    job_type: JobType
    status: JobStatus
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    failed_at: datetime | None
    error_code: str | None
    error_message: str | None
    resume_status: Literal["uploaded", "parsed", "failed"] | None
    retry_available: bool
