from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


HiringVerdict = Literal[
    "strong_hire",
    "hire",
    "consider",
    "insufficient_evidence",
    "do_not_hire",
]

NonEmptyText = Annotated[str, Field(min_length=1, max_length=400)]
SummaryText = Annotated[str, Field(min_length=1, max_length=1200)]
NextActionText = Annotated[str, Field(min_length=1, max_length=400)]


class AiHiringIntelligenceResponse(BaseModel):
    """Executive hiring decision report for a hiring manager."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    verdict: HiringVerdict
    confidence: int = Field(ge=0, le=100)
    executive_summary: SummaryText
    strengths: list[NonEmptyText] = Field(default_factory=list, max_length=5)
    hiring_risks: list[NonEmptyText] = Field(default_factory=list, max_length=5)
    confidence_explanation: list[NonEmptyText] = Field(default_factory=list, max_length=5)
    first_90_days_focus: list[NonEmptyText] = Field(default_factory=list, max_length=5)
    recommended_next_action: NextActionText
