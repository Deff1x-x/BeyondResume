"""Immutable result contracts for future GitHub skill re-extraction stages."""

from __future__ import annotations

from dataclasses import dataclass

from app.models.evidence_skill_link import EvidenceSkillLink
from app.models.evidence_unit import EvidenceUnit
from app.services.github_skill_resolution import ResolvedGitHubSkillCandidate
from app.utils.github_skill_extractor import GitHubSkillCandidate


@dataclass(frozen=True, slots=True)
class GitHubUnmatchedManifestSignal:
    signal_type: str
    source_manifest: str
    manifest_kind: str
    ecosystem: str
    source_dependency: str


@dataclass(frozen=True, slots=True)
class GitHubSkillCandidateExtractionResult:
    candidates: tuple[GitHubSkillCandidate, ...]
    unmatched_signals: tuple[GitHubUnmatchedManifestSignal, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.candidates, tuple) or not isinstance(self.unmatched_signals, tuple):
            raise ValueError("GitHub extraction result collections must be tuples")


@dataclass(frozen=True, slots=True)
class GitHubSkillCandidateResolutionResult:
    resolved_candidates: tuple[ResolvedGitHubSkillCandidate, ...]
    unresolved_rule_targets: tuple[GitHubSkillCandidate, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.resolved_candidates, tuple) or not isinstance(
            self.unresolved_rule_targets, tuple
        ):
            raise ValueError("GitHub resolution result collections must be tuples")


@dataclass(frozen=True, slots=True)
class GitHubEvidenceSkillLinkReconciliationResult:
    links: tuple[EvidenceSkillLink, ...]
    created_count: int
    changed_count: int
    unchanged_count: int
    removed_count: int

    def __post_init__(self) -> None:
        _validate_link_result(
            self.links,
            self.created_count,
            self.changed_count,
            self.unchanged_count,
            self.removed_count,
        )


@dataclass(frozen=True, slots=True)
class GitHubSkillExtractionResult:
    evidence_unit: EvidenceUnit
    extraction_version: str
    links: tuple[EvidenceSkillLink, ...]
    created_count: int
    changed_count: int
    unchanged_count: int
    removed_count: int
    unmatched_signals: tuple[GitHubUnmatchedManifestSignal, ...]
    unresolved_rule_targets: tuple[GitHubSkillCandidate, ...]

    def __post_init__(self) -> None:
        _validate_link_result(
            self.links,
            self.created_count,
            self.changed_count,
            self.unchanged_count,
            self.removed_count,
        )
        if not isinstance(self.unmatched_signals, tuple) or not isinstance(
            self.unresolved_rule_targets, tuple
        ):
            raise ValueError("GitHub skill extraction result collections must be tuples")


def _validate_link_result(
    links: tuple[EvidenceSkillLink, ...],
    created_count: int,
    changed_count: int,
    unchanged_count: int,
    removed_count: int,
) -> None:
    if not isinstance(links, tuple):
        raise ValueError("GitHub link result links must be a tuple")
    counts = (created_count, changed_count, unchanged_count, removed_count)
    if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in counts):
        raise ValueError("GitHub link result counters must be non-negative integers")
    if len(links) != created_count + changed_count + unchanged_count:
        raise ValueError("GitHub link result counters must account for every link")
