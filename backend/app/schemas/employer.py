from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class EmployerCompanyCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    company_name: Annotated[str, Field(min_length=1, max_length=160)]
    website: HttpUrl | None = None
    description: Annotated[str | None, Field(default=None, max_length=5000)] = None


class EmployerCompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_name: str
    website: str | None
    description: str | None
    created_at: datetime


VacancyStatus = Literal["draft", "open", "closed"]


class VacancyCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: Annotated[str, Field(min_length=1, max_length=200)]
    description: Annotated[str | None, Field(default=None, max_length=5000)] = None
    status: VacancyStatus = "open"


class VacancyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    status: VacancyStatus
    created_at: datetime


VacancyRequirementType = Literal["required", "preferred"]


class VacancyRequirementCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill_id: UUID
    requirement_type: VacancyRequirementType


class VacancyRequirementResponse(BaseModel):
    id: UUID
    skill_id: UUID
    skill_name: str
    skill_category: str
    requirement_type: VacancyRequirementType


class SkillOptionResponse(BaseModel):
    id: UUID
    name: str
    category: str


class MatchSkillGroupResponse(BaseModel):
    matched: list[str]
    missing: list[str]


class VacancyMatchResponse(BaseModel):
    candidate_id: UUID
    candidate_name: str
    score: int
    required: MatchSkillGroupResponse
    preferred: MatchSkillGroupResponse


class VacancyMatchesResponse(BaseModel):
    matches: list[VacancyMatchResponse]


class MatchDetailsCandidateResponse(BaseModel):
    id: UUID
    name: str
    headline: str | None
    avatar: str | None


class MatchDetailsMatchResponse(BaseModel):
    score: int
    required: MatchSkillGroupResponse
    preferred: MatchSkillGroupResponse


class MatchDetailsPassportResponse(BaseModel):
    top_skills: list[str]


class MatchDetailsEvidenceResponse(BaseModel):
    source_type: str
    title: str | None
    skills: list[str]


class MatchDetailsRoadmapItemResponse(BaseModel):
    id: str
    title: str
    reason: str
    priority: Literal["high", "medium", "low"]
    missing_skills: list[str]
    related_skills: list[str]


class MatchDetailsResponse(BaseModel):
    candidate: MatchDetailsCandidateResponse
    match: MatchDetailsMatchResponse
    passport: MatchDetailsPassportResponse
    evidence: list[MatchDetailsEvidenceResponse]
    roadmap: list[MatchDetailsRoadmapItemResponse]


class AiMatchExplanationResponse(BaseModel):
    summary: str
    strengths: list[str]
    gaps: list[str]
    next_steps: list[str]
