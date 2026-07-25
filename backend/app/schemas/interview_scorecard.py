"""Schemas for employer Interview Scorecard."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


InterviewRecommendation = Literal["strong_yes", "yes", "mixed", "no"]

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

    technical_competency: ScoreRating
    experience_relevance: ScoreRating
    communication: ScoreRating
    ownership: ScoreRating
    interview_summary: str | None = None
    interview_notes: str | None = None
    recommendation: InterviewRecommendation

    @field_validator("interview_summary", mode="before")
    @classmethod
    def normalize_summary(cls, value: object) -> str | None:
        return _normalize_optional_text(value, max_length=1200)

    @field_validator("interview_notes", mode="before")
    @classmethod
    def normalize_notes(cls, value: object) -> str | None:
        return _normalize_optional_text(value, max_length=5000)


class InterviewScorecardResponse(BaseModel):
    """Public interview scorecard DTO."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    vacancy_id: UUID
    candidate_id: UUID
    technical_competency: int
    experience_relevance: int
    communication: int
    ownership: int
    interview_summary: str | None
    interview_notes: str | None
    recommendation: InterviewRecommendation
    created_at: datetime
    updated_at: datetime
