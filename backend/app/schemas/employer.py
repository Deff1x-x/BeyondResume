from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class EmployerCompanyCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    company_name: Annotated[str, Field(min_length=1, max_length=160)]
    website: HttpUrl | None = None
    description: Annotated[str | None, Field(default=None, max_length=5000)] = None


class EmployerCompanyUpdateRequest(BaseModel):
    """Partial update of existing company fields. Omitted fields stay unchanged."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    company_name: Annotated[str | None, Field(default=None, min_length=1, max_length=160)] = None
    website: HttpUrl | None = None
    description: Annotated[str | None, Field(default=None, max_length=5000)] = None

    @field_validator("company_name", mode="before")
    @classmethod
    def reject_null_company_name(cls, value: object) -> object:
        if value is None:
            raise ValueError("company_name cannot be null")
        return value


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


class SignalSummaryResponse(BaseModel):
    """Employer-safe public category describing why evidence supports a skill."""

    category: str


class MatchedSkillEvidenceResponse(BaseModel):
    """Employer-safe evidence unit supporting one matched vacancy skill."""

    id: UUID
    source_type: str
    title: str | None
    verification_status: str | None
    ownership_status: str | None
    evidence_confidence: float
    signal_summaries: list[SignalSummaryResponse] = Field(default_factory=list)


class MatchedSkillDetailsResponse(BaseModel):
    skill_id: UUID
    skill_name: str
    evidence: list[MatchedSkillEvidenceResponse]


class EvidenceSuggestionResponse(BaseModel):
    """One public evidence category that could confirm a missing skill."""

    category: str


class MissingSkillDetailsResponse(BaseModel):
    """Deterministic evidence channels for one skill absent from the passport."""

    skill_id: UUID
    skill_name: str
    evidence_suggestions: list[EvidenceSuggestionResponse]


class MatchSkillGroupResponse(BaseModel):
    matched: list[str]
    missing: list[str]
    matched_details: list[MatchedSkillDetailsResponse] = Field(default_factory=list)
    missing_details: list[MissingSkillDetailsResponse] = Field(default_factory=list)


class VacancyMatchResponse(BaseModel):
    candidate_id: UUID
    candidate_name: str
    score: int
    required: MatchSkillGroupResponse
    preferred: MatchSkillGroupResponse


class VacancyMatchesResponse(BaseModel):
    matches: list[VacancyMatchResponse]


EmployerCandidateStage = Literal[
    "shortlisted",
    "screening",
    "interview",
    "offer",
    "hired",
    "rejected",
]


class EmployerShortlistStageUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stage: EmployerCandidateStage


class EmployerShortlistNoteUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    note: str | None

    @field_validator("note", mode="before")
    @classmethod
    def normalize_note(cls, value: object) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("Input should be a valid string")
        stripped = value.strip()
        if stripped == "":
            return None
        if len(stripped) > 5000:
            raise ValueError("String should have at most 5000 characters")
        return stripped


class EmployerShortlistEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vacancy_id: UUID
    candidate_id: UUID
    stage: EmployerCandidateStage
    note: str | None
    created_at: datetime
    updated_at: datetime


class EmployerShortlistListResponse(BaseModel):
    entries: list[EmployerShortlistEntryResponse]


class MatchDetailsCandidateResponse(BaseModel):
    id: UUID
    name: str
    headline: str | None
    avatar: str | None


class MatchDetailsMatchResponse(BaseModel):
    score: int
    required: MatchSkillGroupResponse
    preferred: MatchSkillGroupResponse


class MatchDetailsPassportSkillResponse(BaseModel):
    """Employer-safe, read-only projection of an existing passport skill."""

    name: str
    evidence_confidence: float
    evidence_count: int
    source_types: list[str]


class MatchDetailsPassportResponse(BaseModel):
    # Retained for existing match-review clients.
    top_skills: list[str]
    # Values come directly from the candidate's existing Skill Passport.
    skills: list[MatchDetailsPassportSkillResponse] = []


class MatchDetailsEvidenceResponse(BaseModel):
    source_type: str
    title: str | None
    verification_status: str | None
    ownership_status: str | None
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
    has_applied: bool = False


ApplicationStatus = Literal["applied", "withdrawn"]


class EmployerApplicantResponse(BaseModel):
    application_id: UUID
    candidate_id: UUID
    candidate_name: str
    status: ApplicationStatus
    applied_at: datetime
    score: int
    required: MatchSkillGroupResponse
    preferred: MatchSkillGroupResponse


class EmployerApplicantsResponse(BaseModel):
    applicants: list[EmployerApplicantResponse]


class ApplicantContactResponse(BaseModel):
    email: str
    phone: str | None
    telegram: str | None
    linkedin_url: str | None
    portfolio_url: str | None
    location: str | None


class AiMatchExplanationResponse(BaseModel):
    summary: str
    strengths: list[str]
    gaps: list[str]
    next_steps: list[str]
