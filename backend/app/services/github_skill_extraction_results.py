"""Immutable result contracts for future GitHub skill re-extraction stages."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Sequence

from app.models.evidence_skill_link import EvidenceSkillLink
from app.models.evidence_unit import EvidenceUnit
from app.services.github_skill_resolution import (
    ResolvedGitHubSkillCandidate,
    resolve_github_skill_candidates,
)
from app.utils.github_skill_extractor import (
    GitHubSkillCandidate,
    extract_github_skill_candidates,
)
from app.utils.github_skill_rules import (
    DEPENDENCY_MANIFEST_SIGNAL_TYPE,
    GitHubDeterministicSkillRule,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.integrations.github import GitHubRepositorySnapshot


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


def extract_github_skill_candidate_extraction_result(
    snapshot: GitHubRepositorySnapshot,
    *,
    rules: tuple[GitHubDeterministicSkillRule, ...],
) -> GitHubSkillCandidateExtractionResult:
    """Return matched candidates and unmatched normalized manifest signals."""
    candidates = extract_github_skill_candidates(snapshot, rules=rules)
    matched_signal_keys = {_candidate_signal_key(candidate) for candidate in candidates}
    unmatched_signals = tuple(
        sorted(
            (
                GitHubUnmatchedManifestSignal(
                    signal_type=DEPENDENCY_MANIFEST_SIGNAL_TYPE,
                    source_manifest=manifest.path,
                    manifest_kind=manifest.kind,
                    ecosystem=manifest.ecosystem,
                    source_dependency=dependency.name,
                )
                for manifest in snapshot.normalized_manifests
                for dependency in manifest.dependencies
                if _manifest_signal_key(
                    manifest.path, manifest.kind, manifest.ecosystem, dependency.name
                )
                not in matched_signal_keys
            ),
            key=_unmatched_signal_sort_key,
        )
    )
    return GitHubSkillCandidateExtractionResult(
        candidates=candidates,
        unmatched_signals=unmatched_signals,
    )


def resolve_github_skill_candidate_resolution_result(
    session: Session,
    candidates: Sequence[GitHubSkillCandidate],
) -> GitHubSkillCandidateResolutionResult:
    """Return canonical resolutions and candidates not resolved by the ontology."""
    resolved_candidates = resolve_github_skill_candidates(session, candidates)
    resolved_source_candidates = {resolved.candidate for resolved in resolved_candidates}
    unresolved_rule_targets = tuple(
        sorted(
            (candidate for candidate in candidates if candidate not in resolved_source_candidates),
            key=_candidate_source_sort_key,
        )
    )
    return GitHubSkillCandidateResolutionResult(
        resolved_candidates=resolved_candidates,
        unresolved_rule_targets=unresolved_rule_targets,
    )


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


def _candidate_signal_key(candidate: GitHubSkillCandidate) -> tuple[str, str, str, str, str]:
    return _manifest_signal_key(
        candidate.source_manifest,
        candidate.manifest_kind,
        candidate.ecosystem,
        candidate.source_dependency,
    )


def _manifest_signal_key(
    source_manifest: str,
    manifest_kind: str,
    ecosystem: str,
    source_dependency: str,
) -> tuple[str, str, str, str, str]:
    return (
        DEPENDENCY_MANIFEST_SIGNAL_TYPE,
        source_manifest,
        manifest_kind,
        ecosystem,
        source_dependency,
    )


def _unmatched_signal_sort_key(
    signal: GitHubUnmatchedManifestSignal,
) -> tuple[str, str, str, str, str]:
    return (
        signal.signal_type,
        signal.source_manifest,
        signal.manifest_kind,
        signal.ecosystem,
        signal.source_dependency,
    )


def _candidate_source_sort_key(
    candidate: GitHubSkillCandidate,
) -> tuple[str, str, str, str, str, str, str]:
    return (
        candidate.signal_type,
        candidate.source_manifest,
        candidate.manifest_kind,
        candidate.ecosystem,
        candidate.source_dependency,
        candidate.rule_id,
        candidate.target_skill_name,
    )
