from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

CompanionMode = Literal[
    "target_vacancy", "target_role", "career_growth", "explore_direction"
]
ActionHorizon = Literal["fix_now", "build_next", "grow_further"]
ActionType = Literal[
    "improve_existing_project", "build_new_project", "learn_foundation"
]
ActionStatus = Literal[
    "suggested",
    "accepted",
    "in_progress",
    "awaiting_evidence",
    "evidence_detected",
    "partially_verified",
    "completed",
    "dismissed",
]
GenerationMode = Literal["live", "mock", "fallback"]
SkillRole = Literal["gap", "potential_cover", "related"]


class CareerCompanionGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: CompanionMode
    target_vacancy_id: UUID | None = None
    target_role: str | None = Field(default=None, max_length=120)


class CareerCompanionActionStatusPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal[
        "accepted", "in_progress", "awaiting_evidence", "dismissed"
    ]


class CareerCompanionChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=2000)


class CareerCompanionActionSkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    skill_id: UUID
    skill_name: str
    role: SkillRole


class CareerCompanionActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    horizon: ActionHorizon
    action_type: ActionType
    status: ActionStatus
    title: str
    description: str
    why_it_matters: str
    implementation_steps: list[str]
    expected_artifacts: list[str]
    verification_method: str
    estimated_effort: str
    github_repository_id: UUID | None
    project_label: str | None
    current_target_impact: dict[str, Any]
    career_growth_impact: dict[str, Any]
    priority_score: float
    priority_explanation: str
    sort_order: int
    skills: list[CareerCompanionActionSkillResponse]


class CareerCompanionProgressEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_type: str
    title: str
    detail: str
    payload: dict[str, Any]
    created_at: Any


class CareerCompanionChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: str
    content: str
    revision_applied: str | None
    created_at: Any


class CareerCompanionPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    mode: CompanionMode
    target_vacancy_id: UUID | None
    target_role: str | None
    status: str
    generation_mode: GenerationMode
    summary: dict[str, Any]
    current_position: dict[str, Any]
    actions: list[CareerCompanionActionResponse]
    progress_events: list[CareerCompanionProgressEventResponse]
    chat_messages: list[CareerCompanionChatMessageResponse]


class CareerCompanionChatResponse(BaseModel):
    message: CareerCompanionChatMessageResponse
    plan: CareerCompanionPlanResponse | None = None
