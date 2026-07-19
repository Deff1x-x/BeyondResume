"""Candidate dashboard aggregation over existing domain services.

Does not reimplement passport, roadmap, GitHub scan, or evidence generation.
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.evidence_unit import EvidenceUnit
from app.models.github_repository import GitHubRepository
from app.schemas.dashboard import (
    CandidateDashboardResponse,
    DashboardEvidenceSummary,
    DashboardGitHubSummary,
    DashboardPassportSummary,
    DashboardRoadmapSummary,
)
from app.services.roadmap import build_roadmap_from_passport
from app.services.skill_passport import build_passport, empty_passport

TOP_SKILLS_LIMIT = 4


def build_candidate_dashboard(
    session: Session, candidate_id: UUID | None
) -> CandidateDashboardResponse:
    """Aggregate GitHub, Evidence, Passport, and Roadmap summaries for one candidate."""
    if candidate_id is None:
        return _empty_dashboard()

    passport = build_passport(session, candidate_id)
    roadmap = build_roadmap_from_passport(passport)

    repository_count = session.execute(
        select(func.count())
        .select_from(GitHubRepository)
        .where(GitHubRepository.candidate_id == candidate_id)
    ).scalar_one()
    evidence_count = session.execute(
        select(func.count())
        .select_from(EvidenceUnit)
        .where(EvidenceUnit.candidate_id == candidate_id)
    ).scalar_one()

    top_skills = [skill.name for skill in passport.skills[:TOP_SKILLS_LIMIT]]

    return CandidateDashboardResponse(
        github=DashboardGitHubSummary(
            connected=repository_count > 0,
            repositories=int(repository_count),
        ),
        evidence=DashboardEvidenceSummary(count=int(evidence_count)),
        passport=DashboardPassportSummary(
            skills=passport.total_skills,
            top_skills=top_skills,
        ),
        roadmap=DashboardRoadmapSummary(items=len(roadmap.items)),
    )


def _empty_dashboard() -> CandidateDashboardResponse:
    empty = empty_passport()
    return CandidateDashboardResponse(
        github=DashboardGitHubSummary(connected=False, repositories=0),
        evidence=DashboardEvidenceSummary(count=0),
        passport=DashboardPassportSummary(skills=empty.total_skills, top_skills=[]),
        roadmap=DashboardRoadmapSummary(items=0),
    )
