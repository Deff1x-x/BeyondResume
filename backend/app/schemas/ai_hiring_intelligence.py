from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


TechnicalInterviewRecommendation = Literal[
    "strongly_recommended", "recommended", "conditional", "insufficient_evidence", "not_recommended"
]
InterviewDifficulty = Literal["easy", "medium", "hard"]


class HiringVerdictResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    technical_interview_recommendation: TechnicalInterviewRecommendation
    confidence: int = Field(ge=0, le=100)
    summary: str = Field(min_length=1, max_length=1200)
    strengths: list[str] = Field(default_factory=list, max_length=5)
    concerns: list[str] = Field(default_factory=list, max_length=5)


class InterviewQuestionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    skill: str = Field(min_length=1, max_length=120)
    difficulty: InterviewDifficulty
    question: str = Field(min_length=1, max_length=600)
    reason: str = Field(min_length=1, max_length=400)


class AiHiringIntelligenceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    verdict: HiringVerdictResponse
    interview_questions: list[InterviewQuestionResponse] = Field(default_factory=list, max_length=8)
