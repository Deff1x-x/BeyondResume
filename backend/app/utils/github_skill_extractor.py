"""Pure extraction of rule-backed skill candidates from normalized GitHub manifests."""

from __future__ import annotations

from dataclasses import dataclass

from app.integrations.github import GitHubRepositorySnapshot
from app.utils.github_skill_rules import (
    DEPENDENCY_MANIFEST_SIGNAL_TYPE,
    GITHUB_DETERMINISTIC_SKILL_RULES,
    GitHubDeterministicSkillRule,
    match_github_skill_rule,
)


@dataclass(frozen=True, slots=True)
class GitHubSkillCandidate:
    """One canonical, rule-backed dependency-manifest skill candidate."""

    target_skill_name: str
    source_dependency: str
    source_manifest: str
    manifest_kind: str
    ecosystem: str
    signal_type: str
    rule_id: str


def extract_github_skill_candidates(
    snapshot: GitHubRepositorySnapshot,
    *,
    rules: tuple[GitHubDeterministicSkillRule, ...] = GITHUB_DETERMINISTIC_SKILL_RULES,
) -> tuple[GitHubSkillCandidate, ...]:
    """Extract exact rule matches using only ``snapshot.normalized_manifests``."""
    candidates_by_skill: dict[str, GitHubSkillCandidate] = {}
    for manifest in snapshot.normalized_manifests:
        for dependency in manifest.dependencies:
            rule = match_github_skill_rule(
                signal_type=DEPENDENCY_MANIFEST_SIGNAL_TYPE,
                manifest_kind=manifest.kind,
                ecosystem=manifest.ecosystem,
                normalized_match_value=dependency.name,
                rules=rules,
            )
            if rule is None:
                continue
            candidate = GitHubSkillCandidate(
                target_skill_name=rule.target_skill_name,
                source_dependency=dependency.name,
                source_manifest=manifest.path,
                manifest_kind=manifest.kind,
                ecosystem=manifest.ecosystem,
                signal_type=DEPENDENCY_MANIFEST_SIGNAL_TYPE,
                rule_id=rule.rule_id,
            )
            existing = candidates_by_skill.get(candidate.target_skill_name)
            if existing is None or _candidate_key(candidate) < _candidate_key(existing):
                candidates_by_skill[candidate.target_skill_name] = candidate
    return tuple(sorted(candidates_by_skill.values(), key=_candidate_key))


def _candidate_key(candidate: GitHubSkillCandidate) -> tuple[str, str, str, str, str, str]:
    return (
        candidate.target_skill_name,
        candidate.source_manifest,
        candidate.manifest_kind,
        candidate.ecosystem,
        candidate.source_dependency,
        candidate.signal_type,
    )
