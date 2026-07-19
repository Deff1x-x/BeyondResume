from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.resume import JobPollingResponse


class GitHubRepositoryConnectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    repository_url: Annotated[str, Field(min_length=1, max_length=2048)]


class GitHubRepositoryResponse(BaseModel):
    id: UUID
    repository_url: str
    created_at: datetime
    job: JobPollingResponse | None


class GitHubRepositorySnapshotSummary(BaseModel):
    description: str | None
    is_archived: bool | None
    languages: list[str]
    file_count: int
    manifest_count: int


class GitHubRepositorySkillResponse(BaseModel):
    name: str
    category: str
    extraction_confidence: float


class GitHubRepositoryDetailResponse(GitHubRepositoryResponse):
    snapshot: GitHubRepositorySnapshotSummary | None
    skills: list[GitHubRepositorySkillResponse]
