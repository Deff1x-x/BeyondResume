from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class EmployerCompanyCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    company_name: Annotated[str, Field(min_length=1, max_length=160)]
    website: HttpUrl | None = None
    description: Annotated[str | None, Field(default=None, max_length=5000)] = None


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
