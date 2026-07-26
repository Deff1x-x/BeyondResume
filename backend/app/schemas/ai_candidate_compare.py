"""Schemas for AI Candidate Compare (LLM payload + API response)."""

from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


GenerationMode = Literal["live", "mock"]
CompareConfidence = Literal["low", "medium", "high"]

NonEmptyText = Annotated[str, Field(min_length=1, max_length=400)]
SummaryText = Annotated[str, Field(min_length=1, max_length=1200)]
FactRef = Annotated[str, Field(min_length=1, max_length=200)]
QuestionText = Annotated[str, Field(min_length=1, max_length=300)]


class AiCandidateCompareRequest(BaseModel):
    """Employer request to compare 2–4 shortlisted candidates with AI."""

    model_config = ConfigDict(extra="forbid")

    candidate_ids: list[UUID] = Field(min_length=2, max_length=4)

    @field_validator("candidate_ids")
    @classmethod
    def reject_duplicate_candidate_ids(cls, value: list[UUID]) -> list[UUID]:
        if len(value) != len(set(value)):
            raise ValueError("candidate_ids must not contain duplicates")
        return value


class GroundedInsight(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    text: NonEmptyText
    fact_refs: list[FactRef] = Field(min_length=1, max_length=8)


class GroundedQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    question: QuestionText
    candidate_ids: list[UUID] = Field(min_length=1, max_length=4)
    fact_refs: list[FactRef] = Field(min_length=1, max_length=8)

    @field_validator("candidate_ids")
    @classmethod
    def reject_duplicate_question_candidates(cls, value: list[UUID]) -> list[UUID]:
        if len(value) != len(set(value)):
            raise ValueError("candidate_ids must not contain duplicates")
        return value


class CandidateAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    candidate_id: UUID
    strengths: list[GroundedInsight] = Field(default_factory=list, max_length=4)
    risks: list[GroundedInsight] = Field(default_factory=list, max_length=4)


class HiringRecommendation(BaseModel):
    """Structured advisory hiring recommendation grounded in INPUT evidence."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    why_leads: list[GroundedInsight] = Field(min_length=1, max_length=4)
    main_risk: GroundedInsight
    interview_focus: list[GroundedInsight] = Field(min_length=1, max_length=5)
    alternative_outcome: GroundedInsight


class AiCandidateCompareLlmPayload(BaseModel):
    """Structured Outputs contract produced by the LLM (no generation_mode)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    summary: SummaryText
    candidate_assessments: list[CandidateAssessment] = Field(min_length=2, max_length=4)
    key_differences: list[GroundedInsight] = Field(default_factory=list, max_length=6)
    interview_focus_questions: list[GroundedQuestion] = Field(
        default_factory=list, max_length=6
    )
    recommended_candidate_id: UUID
    hiring_recommendation: HiringRecommendation
    confidence: CompareConfidence
    uncertainties: list[GroundedInsight] = Field(default_factory=list, max_length=5)


class AiCandidateCompareResponse(AiCandidateCompareLlmPayload):
    """API response: LLM payload plus backend-owned metadata."""

    vacancy_id: UUID
    candidate_ids: list[UUID] = Field(min_length=2, max_length=4)
    generation_mode: GenerationMode
