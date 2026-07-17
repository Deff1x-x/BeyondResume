from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


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
