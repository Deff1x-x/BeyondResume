"""Orchestration of deterministic GitHub EvidenceSkillLink persistence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.evidence_unit import EvidenceUnit
from app.services.evidence_skill_links import EvidenceSkillLinkPersistenceResult
from app.services.github_evidence_commands import build_github_evidence_commands
from app.services.github_evidence_persistence_adapter import persist_github_evidence_skill_link
from app.services.github_evidence_skill_link_builder import build_github_skill_link_values
from app.services.github_skill_resolution import ResolvedGitHubSkillCandidate


@dataclass(frozen=True, slots=True)
class GitHubEvidenceSkillLinkOrchestrationResult:
    """Ordered persistence outcomes for factory-produced GitHub evidence commands."""

    persistence_results: tuple[EvidenceSkillLinkPersistenceResult, ...]


def persist_resolved_github_skill_candidates(
    session: Session,
    *,
    candidate_id: UUID,
    evidence_unit: EvidenceUnit,
    resolved_candidates: Sequence[ResolvedGitHubSkillCandidate],
) -> GitHubEvidenceSkillLinkOrchestrationResult:
    """Persist the commands produced from already resolved GitHub source signals."""
    commands = build_github_evidence_commands(
        candidate_id=candidate_id,
        evidence_unit=evidence_unit,
        resolved_candidates=resolved_candidates,
    )
    persistence_results = tuple(
        persist_github_evidence_skill_link(session, build_github_skill_link_values(command))
        for command in commands
    )
    return GitHubEvidenceSkillLinkOrchestrationResult(persistence_results=persistence_results)
