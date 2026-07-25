"""Schemas for AI Interview Questions."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


InterviewQuestionCategory = Literal[
    "technical",
    "experience",
    "risk_validation",
    "ownership",
]


def _normalize_required_text(value: object, *, max_length: int) -> str:
    if not isinstance(value, str):
        raise ValueError("Input should be a valid string")
    stripped = " ".join(value.split()).strip()
    if stripped == "":
        raise ValueError("String should not be empty")
    if len(stripped) > max_length:
        raise ValueError(f"String should have at most {max_length} characters")
    return stripped


def _normalize_optional_text(value: object, *, max_length: int) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("Input should be a valid string")
    stripped = " ".join(value.split()).strip()
    if stripped == "":
        return None
    if len(stripped) > max_length:
        raise ValueError(f"String should have at most {max_length} characters")
    return stripped


QuestionText = Annotated[str, Field(min_length=1, max_length=280)]
ReasonText = Annotated[str, Field(min_length=1, max_length=400)]
SkillText = Annotated[str, Field(min_length=1, max_length=80)]
EvidenceText = Annotated[str, Field(min_length=1, max_length=200)]


class InterviewQuestion(BaseModel):
    """One interview-ready question with rationale."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    category: InterviewQuestionCategory
    question: QuestionText
    reason: ReasonText
    target_skill: SkillText | None = None
    evidence_basis: EvidenceText | None = None

    @field_validator("question", mode="before")
    @classmethod
    def normalize_question(cls, value: object) -> str:
        return _normalize_required_text(value, max_length=280)

    @field_validator("reason", mode="before")
    @classmethod
    def normalize_reason(cls, value: object) -> str:
        return _normalize_required_text(value, max_length=400)

    @field_validator("target_skill", mode="before")
    @classmethod
    def normalize_target_skill(cls, value: object) -> str | None:
        return _normalize_optional_text(value, max_length=80)

    @field_validator("evidence_basis", mode="before")
    @classmethod
    def normalize_evidence_basis(cls, value: object) -> str | None:
        return _normalize_optional_text(value, max_length=200)


class InterviewQuestionsResponse(BaseModel):
    """Public interview-prep questions for one vacancy and candidate."""

    model_config = ConfigDict(extra="forbid")

    questions: list[InterviewQuestion] = Field(min_length=1, max_length=8)

    @model_validator(mode="after")
    def reject_duplicate_questions(self) -> InterviewQuestionsResponse:
        seen: set[str] = set()
        for item in self.questions:
            identity = " ".join(item.question.split()).casefold()
            if identity in seen:
                raise ValueError("Duplicate interview questions are not allowed")
            seen.add(identity)
        return self
