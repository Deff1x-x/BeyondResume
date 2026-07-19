from uuid import UUID

from pydantic import BaseModel


class SkillPassportEvidenceResponse(BaseModel):
    id: UUID
    title: str | None
    description: str | None
    source_type: str
    source_reference: str | None
    evidence_confidence: float


class SkillPassportSkillResponse(BaseModel):
    id: UUID
    name: str
    category: str
    evidence_confidence: float
    evidence_count: int
    evidence: list[SkillPassportEvidenceResponse]


class SkillPassportResponse(BaseModel):
    skills: list[SkillPassportSkillResponse]
    total_skills: int
    total_evidence: int
