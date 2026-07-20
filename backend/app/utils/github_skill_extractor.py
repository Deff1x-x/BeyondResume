"""Deterministic extraction from normalized manifests and bounded source files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Iterable

from app.integrations.github import GitHubRepositorySnapshot
from app.utils.github_code_usage_rules import (
    GITHUB_CODE_USAGE_RULES,
    GitHubCodeUsageRule,
    is_excluded_analysis_path,
    is_test_path,
)
from app.utils.github_skill_rules import (
    DEPENDENCY_MANIFEST_SIGNAL_TYPE,
    GITHUB_DETERMINISTIC_SKILL_RULES,
    GitHubDeterministicSkillRule,
    match_github_skill_rule,
)


@dataclass(frozen=True, slots=True)
class GitHubSkillCandidate:
    """One canonical, rule-backed GitHub source signal candidate."""

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
    code_rules: tuple[GitHubCodeUsageRule, ...] = GITHUB_CODE_USAGE_RULES,
) -> tuple[GitHubSkillCandidate, ...]:
    """Extract stable manifest and actual bounded code/configuration signals."""
    candidates = [*_manifest_candidates(snapshot, rules), *_code_candidates(snapshot, code_rules)]
    candidates_by_signal = {_candidate_key(candidate): candidate for candidate in candidates}
    return tuple(sorted(candidates_by_signal.values(), key=_candidate_key))


def _manifest_candidates(
    snapshot: GitHubRepositorySnapshot, rules: tuple[GitHubDeterministicSkillRule, ...]
) -> Iterable[GitHubSkillCandidate]:
    for manifest in snapshot.normalized_manifests:
        for dependency in manifest.dependencies:
            rule = match_github_skill_rule(
                signal_type=DEPENDENCY_MANIFEST_SIGNAL_TYPE,
                manifest_kind=manifest.kind,
                ecosystem=manifest.ecosystem,
                normalized_match_value=dependency.name,
                rules=rules,
            )
            if rule is not None:
                yield GitHubSkillCandidate(
                    target_skill_name=rule.target_skill_name,
                    source_dependency=dependency.name,
                    source_manifest=manifest.path,
                    manifest_kind=manifest.kind,
                    ecosystem=manifest.ecosystem,
                    signal_type=DEPENDENCY_MANIFEST_SIGNAL_TYPE,
                    rule_id=rule.rule_id,
                )


def _code_candidates(
    snapshot: GitHubRepositorySnapshot, rules: tuple[GitHubCodeUsageRule, ...]
) -> Iterable[GitHubSkillCandidate]:
    for path, content in sorted(snapshot.source_files):
        if is_excluded_analysis_path(path):
            continue
        extension = PurePosixPath(path).suffix.lower()
        name = path.lower().rsplit("/", 1)[-1]
        is_ci = path.lower().startswith(".github/workflows/") and name.endswith((".yml", ".yaml"))
        is_test = is_test_path(path)
        for rule in rules:
            if extension in rule.extensions:
                if not rule.imports and not rule.api_calls and not rule.class_or_function_usage:
                    yield _candidate(
                        rule,
                        path,
                        "test_usage" if is_test else "source_function_usage",
                        "test_usage" if is_test else "source_file",
                    )
                yield from _pattern_candidates(rule, path, content, rule.imports, "source_import", is_test)
                yield from _pattern_candidates(rule, path, content, rule.api_calls, "source_api_call", is_test)
                yield from _pattern_candidates(
                    rule, path, content, rule.class_or_function_usage, "source_class_usage", is_test
                )
            if any(pattern.search(path) for pattern in rule.config_files) and (
                not rule.config_patterns or any(pattern.search(content) for pattern in rule.config_patterns)
            ):
                yield _candidate(rule, path, "configuration_usage", "configuration")
            if is_ci:
                yield from _pattern_candidates(rule, path, content, rule.ci_patterns, "ci", False)
        if name in {"dockerfile", "docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml", ".dockerignore"}:
            yield GitHubSkillCandidate(
                target_skill_name="Docker",
                source_dependency="docker_artifact",
                source_manifest=path,
                manifest_kind="source_file",
                ecosystem="github",
                signal_type="docker",
                rule_id="gh_rule.code.docker.artifact.v1",
            )
        if is_ci and "docker" in content.lower():
            yield GitHubSkillCandidate(
                target_skill_name="Docker",
                source_dependency="docker_ci",
                source_manifest=path,
                manifest_kind="source_file",
                ecosystem="github",
                signal_type="ci",
                rule_id="gh_rule.code.docker.ci.v1",
            )
        if is_ci:
            yield GitHubSkillCandidate(
                target_skill_name="GitHub Actions",
                source_dependency="workflow",
                source_manifest=path,
                manifest_kind="source_file",
                ecosystem="github",
                signal_type="ci",
                rule_id="gh_rule.code.github_actions.workflow.v1",
            )


def _pattern_candidates(
    rule: GitHubCodeUsageRule,
    path: str,
    content: str,
    patterns: tuple[object, ...],
    signal_type: str,
    is_test: bool,
) -> Iterable[GitHubSkillCandidate]:
    if not any(getattr(pattern, "search")(content) for pattern in patterns):
        return ()
    yield _candidate(
        rule,
        path,
        "test_usage" if is_test else signal_type,
        "test_usage" if is_test else signal_type,
    )


def _candidate(
    rule: GitHubCodeUsageRule, path: str, signal_type: str, matched_value: str
) -> GitHubSkillCandidate:
    rule_suffix = signal_type.replace("_usage", "").replace("_", ".")
    return GitHubSkillCandidate(
        target_skill_name=rule.target_skill_name,
        source_dependency=matched_value,
        source_manifest=path,
        manifest_kind="source_file",
        ecosystem="github",
        signal_type=signal_type,
        rule_id=f"gh_rule.code.{rule.target_skill_name.lower().replace('.', '').replace(' ', '_')}.{rule_suffix}.v1",
    )


def _candidate_key(candidate: GitHubSkillCandidate) -> tuple[str, str, str, str, str, str, str]:
    return (
        candidate.signal_type,
        candidate.target_skill_name,
        candidate.source_manifest,
        candidate.manifest_kind,
        candidate.ecosystem,
        candidate.source_dependency,
        candidate.rule_id,
    )
