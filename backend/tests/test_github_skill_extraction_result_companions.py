from inspect import getsource
from unittest.mock import Mock

import pytest

from app.integrations.github import GitHubRepositorySnapshot
from app.services.github_skill_extraction_results import (
    extract_github_skill_candidate_extraction_result,
    resolve_github_skill_candidate_resolution_result,
)
from app.services.github_skill_resolution import ResolvedGitHubSkillCandidate
from app.utils.github_manifests import GitHubNormalizedDependency, GitHubNormalizedManifest
from app.utils.github_skill_extractor import GitHubSkillCandidate
from app.utils.github_skill_rules import GitHubDeterministicSkillRule
import app.services.github_skill_extraction_results as results_module


def snapshot(*manifests: GitHubNormalizedManifest) -> GitHubRepositorySnapshot:
    return GitHubRepositorySnapshot(
        canonical_url="https://github.com/octo/example",
        repository_name="example",
        owner="octo",
        description=None,
        default_branch="main",
        is_public=True,
        is_archived=False,
        languages=(),
        file_tree=(),
        readme_text=None,
        manifest_paths=tuple(manifest.path for manifest in manifests),
        is_demo=False,
        normalized_manifests=manifests,
    )


def manifest(path: str, *dependencies: str) -> GitHubNormalizedManifest:
    return GitHubNormalizedManifest(
        path=path,
        kind="package_json",
        ecosystem="npm",
        dependencies=tuple(
            GitHubNormalizedDependency(name=dependency, section=None, metadata={})
            for dependency in dependencies
        ),
    )


def rule(dependency: str, target: str = "React") -> GitHubDeterministicSkillRule:
    return GitHubDeterministicSkillRule(
        rule_id=f"gh_rule.package.{dependency}.v1",
        signal_type="dependency_manifest",
        manifest_kind="package_json",
        ecosystem="npm",
        normalized_match_value=dependency,
        target_skill_name=target,
    )


def candidate(
    target: str,
    dependency: str,
    manifest_path: str,
    rule_id: str,
) -> GitHubSkillCandidate:
    return GitHubSkillCandidate(
        target_skill_name=target,
        source_dependency=dependency,
        source_manifest=manifest_path,
        manifest_kind="package_json",
        ecosystem="npm",
        signal_type="dependency_manifest",
        rule_id=rule_id,
    )


def test_extraction_companion_calls_canonical_extractor_once_and_classifies_unmatched(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_snapshot = snapshot(
        manifest("z/package.json", "unknown-z"),
        manifest("a/package.json", "react", "unknown-a"),
    )
    canonical_extractor = results_module.extract_github_skill_candidates
    extractor = Mock(wraps=canonical_extractor)
    monkeypatch.setattr(results_module, "extract_github_skill_candidates", extractor)

    result = extract_github_skill_candidate_extraction_result(
        source_snapshot,
        rules=(rule("react"),),
    )

    extractor.assert_called_once_with(source_snapshot, rules=(rule("react"),))
    assert tuple(item.source_dependency for item in result.candidates) == ("react",)
    assert tuple(item.source_dependency for item in result.unmatched_signals) == (
        "unknown-a",
        "unknown-z",
    )
    assert isinstance(result.candidates, tuple)
    assert isinstance(result.unmatched_signals, tuple)


def test_extraction_companion_preserves_canonical_candidate_order_and_empty_results() -> None:
    source_snapshot = snapshot(manifest("package.json"))

    result = extract_github_skill_candidate_extraction_result(source_snapshot, rules=())

    assert result.candidates == ()
    assert result.unmatched_signals == ()


def test_extraction_companion_propagates_canonical_extractor_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error = RuntimeError("extractor failed")
    monkeypatch.setattr(
        results_module,
        "extract_github_skill_candidates",
        Mock(side_effect=error),
    )

    with pytest.raises(RuntimeError, match="extractor failed") as raised:
        extract_github_skill_candidate_extraction_result(snapshot(), rules=())

    assert raised.value is error


def test_resolution_companion_calls_canonical_resolver_once_and_sorts_unresolved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    resolved_candidate = candidate("React", "react", "z/package.json", "gh_rule.package.react.v1")
    unresolved_later = candidate("Vue", "vue", "z/package.json", "gh_rule.package.vue.v1")
    unresolved_earlier = candidate(
        "Angular", "angular", "a/package.json", "gh_rule.package.angular.v1"
    )
    resolved = Mock(spec=ResolvedGitHubSkillCandidate)
    resolved.candidate = resolved_candidate
    resolver = Mock(return_value=(resolved,))
    monkeypatch.setattr(results_module, "resolve_github_skill_candidates", resolver)
    session = Mock()

    result = resolve_github_skill_candidate_resolution_result(
        session,
        (unresolved_later, resolved_candidate, unresolved_earlier),
    )

    resolver.assert_called_once_with(
        session,
        (unresolved_later, resolved_candidate, unresolved_earlier),
    )
    assert result.resolved_candidates == (resolved,)
    assert result.unresolved_rule_targets == (unresolved_earlier, unresolved_later)
    assert isinstance(result.resolved_candidates, tuple)
    assert isinstance(result.unresolved_rule_targets, tuple)


def test_resolution_companion_propagates_canonical_resolver_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error = RuntimeError("resolver failed")
    monkeypatch.setattr(
        results_module,
        "resolve_github_skill_candidates",
        Mock(side_effect=error),
    )

    with pytest.raises(RuntimeError, match="resolver failed") as raised:
        resolve_github_skill_candidate_resolution_result(Mock(), ())

    assert raised.value is error


def test_companions_contain_no_direct_matching_resolution_or_persistence_logic() -> None:
    source = getsource(results_module)

    assert "match_github_skill_rule" not in source
    assert "resolve_skill" not in source
    assert "select" not in source
    assert ".execute(" not in source
    assert ".flush(" not in source
    assert ".commit(" not in source
    assert ".rollback(" not in source
    assert "reconcile_" not in source
