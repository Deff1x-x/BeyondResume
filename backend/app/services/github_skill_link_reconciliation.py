"""Scoped reconciliation for deterministic GitHub evidence skill links."""

from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evidence_skill_link import EvidenceSkillLink
from app.models.evidence_unit import EvidenceUnit
from app.services.github_evidence_commands import (
    GITHUB_DETERMINISTIC_EXTRACTION_METHOD,
    GITHUB_DETERMINISTIC_EXTRACTION_VERSION,
)
from app.services.github_evidence_skill_link_orchestration import (
    persist_resolved_github_skill_candidates,
)
from app.services.github_skill_extraction_results import (
    GitHubEvidenceSkillLinkReconciliationResult,
)
from app.services.github_skill_resolution import ResolvedGitHubSkillCandidate


def reconcile_github_evidence_skill_links(
    session: Session,
    *,
    candidate_id: UUID,
    evidence_unit: EvidenceUnit,
    resolved_candidates: Sequence[ResolvedGitHubSkillCandidate],
) -> GitHubEvidenceSkillLinkReconciliationResult:
    """Persist the desired GitHub links and remove stale links in the strict scope."""
    existing_links = tuple(
        session.execute(
            select(EvidenceSkillLink).where(
                EvidenceSkillLink.candidate_id == candidate_id,
                EvidenceSkillLink.evidence_unit_id == evidence_unit.id,
                EvidenceSkillLink.extraction_method == GITHUB_DETERMINISTIC_EXTRACTION_METHOD,
                EvidenceSkillLink.extraction_version == GITHUB_DETERMINISTIC_EXTRACTION_VERSION,
            )
        )
        .scalars()
        .all()
    )
    orchestration_result = persist_resolved_github_skill_candidates(
        session,
        candidate_id=candidate_id,
        evidence_unit=evidence_unit,
        resolved_candidates=resolved_candidates,
    )
    persistence_results = orchestration_result.persistence_results
    links = tuple(result.link for result in persistence_results)
    desired_identities = {_link_identity(link) for link in links}
    stale_links = sorted(
        (link for link in existing_links if _link_identity(link) not in desired_identities),
        key=lambda link: str(link.skill_id),
    )
    for stale_link in stale_links:
        session.delete(stale_link)

    return GitHubEvidenceSkillLinkReconciliationResult(
        links=links,
        created_count=sum(result.created and result.changed for result in persistence_results),
        changed_count=sum(not result.created and result.changed for result in persistence_results),
        unchanged_count=sum(
            not result.created and not result.changed for result in persistence_results
        ),
        removed_count=len(stale_links),
    )


def _link_identity(link: EvidenceSkillLink) -> tuple[UUID, UUID, str, str]:
    return (
        link.evidence_unit_id,
        link.skill_id,
        link.extraction_method,
        link.extraction_version,
    )
