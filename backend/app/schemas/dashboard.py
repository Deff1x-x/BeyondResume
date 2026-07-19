from pydantic import BaseModel, Field


class DashboardGitHubSummary(BaseModel):
    connected: bool
    repositories: int = Field(ge=0)


class DashboardEvidenceSummary(BaseModel):
    count: int = Field(ge=0)


class DashboardPassportSummary(BaseModel):
    skills: int = Field(ge=0)
    top_skills: list[str]


class DashboardRoadmapSummary(BaseModel):
    items: int = Field(ge=0)


class CandidateDashboardResponse(BaseModel):
    github: DashboardGitHubSummary
    evidence: DashboardEvidenceSummary
    passport: DashboardPassportSummary
    roadmap: DashboardRoadmapSummary
