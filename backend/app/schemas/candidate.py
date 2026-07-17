from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

WorkFormat = Literal["remote", "hybrid", "onsite", "any"]


class CandidateProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    headline: str | None
    country: str | None
    timezone: str | None
    desired_role: str
    work_format: WorkFormat | None
    bio: str | None


class CandidateProfilePatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    headline: str | None = Field(default=None, max_length=160)
    country: str | None = Field(default=None, max_length=80)
    timezone: str | None = Field(default=None, max_length=60)
    desired_role: str | None = Field(default=None, min_length=1, max_length=80)
    work_format: WorkFormat | None = None
    bio: str | None = None

    @model_validator(mode="after")
    def reject_null_required_fields(self) -> "CandidateProfilePatchRequest":
        for field_name in ("full_name", "desired_role"):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        return self
