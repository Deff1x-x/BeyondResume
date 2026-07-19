from typing import Literal

from pydantic import BaseModel

RoadmapPriority = Literal["high", "medium", "low"]


class RoadmapItemResponse(BaseModel):
    id: str
    title: str
    reason: str
    priority: RoadmapPriority
    missing_skills: list[str]
    related_skills: list[str]


class RoadmapResponse(BaseModel):
    items: list[RoadmapItemResponse]
