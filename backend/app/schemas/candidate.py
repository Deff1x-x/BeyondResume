from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field

from app.models.candidate_profile import OnboardingStatus
from app.schemas.employer import (
    MatchDetailsMatchResponse,
    MatchDetailsRoadmapItemResponse,
)

NonEmptyString = Annotated[str, Field(min_length=1)]


class CandidateProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_name: str | None
    target_role: str | None
    location: str | None
    remote_preference: str | None
    english_level: str | None
    availability: str | None
    summary: str | None
    data_processing_consent: bool | None
    onboarding_status: OnboardingStatus
    salary_expectation: str | None
    preferred_employment_type: str | None
    relocation_readiness: bool | None
    portfolio_url: str | None
    linkedin_url: str | None


class CandidateProfilePatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    display_name: Annotated[str | None, Field(max_length=150, min_length=1)] = None
    target_role: Annotated[str | None, Field(max_length=80, min_length=1)] = None
    location: Annotated[str | None, Field(max_length=80, min_length=1)] = None
    remote_preference: Annotated[str | None, Field(max_length=50, min_length=1)] = None
    english_level: Annotated[str | None, Field(max_length=50, min_length=1)] = None
    availability: Annotated[str | None, Field(max_length=100, min_length=1)] = None
    summary: NonEmptyString | None = None
    data_processing_consent: bool | None = None
    salary_expectation: Annotated[str | None, Field(max_length=100, min_length=1)] = None
    preferred_employment_type: Annotated[str | None, Field(max_length=50, min_length=1)] = None
    relocation_readiness: bool | None = None
    portfolio_url: AnyHttpUrl | None = None
    linkedin_url: AnyHttpUrl | None = None


class CandidateVacancyListItemResponse(BaseModel):
    id: UUID
    title: str
    company_name: str
    description: str | None
    created_at: datetime
    match: MatchDetailsMatchResponse
    required_skills: list[str]
    preferred_skills: list[str]


class CandidateVacancyDetailResponse(CandidateVacancyListItemResponse):
    roadmap: list[MatchDetailsRoadmapItemResponse]
