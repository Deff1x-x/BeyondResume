"""Pure mapping from GitHub evidence commands to link persistence values."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping
from uuid import UUID

from app.services.github_evidence_commands import GitHubEvidenceCommand


@dataclass(frozen=True, slots=True)
class GitHubEvidenceSkillLinkValues:
    """Constructor/update values for one deterministic EvidenceSkillLink."""

    candidate_id: UUID
    evidence_unit_id: UUID
    skill_id: UUID
    extraction_method: str
    extraction_version: str
    extraction_confidence: Decimal
    context: Mapping[str, object]


def build_github_skill_link_values(
    command: GitHubEvidenceCommand,
) -> GitHubEvidenceSkillLinkValues:
    """Copy a command into immutable persistence values without transformation."""
    return GitHubEvidenceSkillLinkValues(
        candidate_id=command.candidate_id,
        evidence_unit_id=command.evidence_unit_id,
        skill_id=command.skill_id,
        extraction_method=command.extraction_method,
        extraction_version=command.extraction_version,
        extraction_confidence=command.extraction_confidence,
        context=command.context,
    )
