from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class EvidenceHubSkillResponse(BaseModel):
    id: UUID
    name: str
    category: str
    extraction_method: str
    evidence_confidence: float


class EvidenceHubSourceResponse(BaseModel):
    label: str
    document_name: str | None = None
    parsed_at: datetime | None = None
    repository_name: str | None = None
    repository_url: str | None = None


class EvidenceHubItemResponse(BaseModel):
    id: UUID
    source_type: str
    source_reference: str | None
    title: str | None
    description: str | None
    verification_status: str | None
    strength: float | None
    created_at: datetime
    updated_at: datetime
    skills: list[EvidenceHubSkillResponse]
    source: EvidenceHubSourceResponse


class EvidenceHubListResponse(BaseModel):
    items: list[EvidenceHubItemResponse]
    total: int
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
