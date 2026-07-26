"""Schemas for employer Interview Scorecard."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


InterviewRecommendation = Literal["strong_yes", "yes", "mixed", "no"]
InterviewScorecardStatus = Literal["draft", "completed"]

ScoreRating = Annotated[int, Field(ge=1, le=5)]


def _normalize_optional_text(value: object, *, max_length: int) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("Input should be a valid string")
    stripped = value.strip()
    if stripped == "":
        return None
    if len(stripped) > max_length:
        raise ValueError(f"String should have at most {max_length} characters")
    return stripped


class InterviewScorecardUpsertRequest(BaseModel):
    """Full replace body for PUT interview scorecard."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    status: InterviewScorecardStatus = "draft"
    technical_competency: ScoreRating | None = None
    experience_relevance: ScoreRating | None = None
    communication: ScoreRating | None = None
    ownership: ScoreRating | None = None
    interview_summary: str | None = None
    interview_notes: str | None = None
    recommendation: InterviewRecommendation | None = None

    @field_validator("interview_summary", mode="before")
    @classmethod
    def normalize_summary(cls, value: object) -> str | None:
        return _normalize_optional_text(value, max_length=1200)

    @field_validator("interview_notes", mode="before")
    @classmethod
    def normalize_notes(cls, value: object) -> str | None:
        return _normalize_optional_text(value, max_length=5000)

    @model_validator(mode="after")
    def require_completed_fields(self) -> Self:
        if self.status != "completed":
            return self
        if (
            self.technical_competency is None
            or self.experience_relevance is None
            or self.communication is None
            or self.ownership is None
            or self.recommendation is None
        ):
            raise ValueError(
                "Completed scorecards require all ratings and a recommendation"
            )
        return self


class InterviewScorecardSummary(BaseModel):
    """Deterministic summary of employer-entered scorecard ratings."""

    model_config = ConfigDict(extra="forbid")

    status: InterviewScorecardStatus
    completed_criteria_count: int
    total_criteria_count: int
    average_rating: float | None
    strongest_dimensions: list[str]
    weakest_dimensions: list[str]
    unanswered_dimensions: list[str]
    recommendation: InterviewRecommendation | None


class InterviewScorecardResponse(BaseModel):
    """Public interview scorecard DTO."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    vacancy_id: UUID
    candidate_id: UUID
    status: InterviewScorecardStatus
    technical_competency: int | None
    experience_relevance: int | None
    communication: int | None
    ownership: int | None
    interview_summary: str | None
    interview_notes: str | None
    recommendation: InterviewRecommendation | None
    summary: InterviewScorecardSummary
    created_at: datetime
    updated_at: datetime
