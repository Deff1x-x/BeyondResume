from dataclasses import FrozenInstanceError
from unittest.mock import Mock

import pytest

from app.models.skill import Skill
from app.services import github_skill_resolution
from app.services.github_skill_resolution import (
    ResolvedGitHubSkillCandidate,
    resolve_github_skill_candidates,
)
from app.utils.github_skill_extractor import GitHubSkillCandidate
from app.utils.github_skill_extractor import extract_github_skill_candidates
from app.integrations.github import GitHubRepositorySnapshot
from app.utils.github_manifests import GitHubNormalizedDependency, GitHubNormalizedManifest
from app.utils.github_skill_rules import (
    DEPENDENCY_MANIFEST_SIGNAL_TYPE,
    GitHubDeterministicSkillRule,
)


def candidate(
    target: str,
    path: str = "package.json",
    rule_id: str = "gh_rule.package.react.v1",
    dependency: str | None = None,
) -> GitHubSkillCandidate:
    return GitHubSkillCandidate(
        target_skill_name=target,
        source_dependency=dependency or target.lower(),
        source_manifest=path,
        manifest_kind="package_json",
        ecosystem="npm",
        signal_type="dependency_manifest",
        rule_id=rule_id,
    )


def skill(name: str) -> Skill:
    return Skill(
        canonical_name=name,
        normalized_name=name.lower(),
        category="framework",
        ontology_version="v1",
    )


def test_resolution_uses_only_resolve_skill_and_returns_persisted_skill(monkeypatch) -> None:
    session = Mock()
    react = skill("React")
    resolver = Mock(return_value=react)
    monkeypatch.setattr(github_skill_resolution, "resolve_skill", resolver)

    result = resolve_github_skill_candidates(session, (candidate("React"),))

    assert result[0].skill is react
    assert result[0].candidate.target_skill_name == "React"
    assert result[0].rule_id == "gh_rule.package.react.v1"
    resolver.assert_called_once_with(session, "React")
    session.add.assert_not_called()
    session.flush.assert_not_called()
    session.commit.assert_not_called()
    session.rollback.assert_not_called()


def test_resolved_candidate_requires_rule_id_and_is_immutable() -> None:
    source_candidate = candidate("React")
    with pytest.raises(TypeError):
        ResolvedGitHubSkillCandidate(skill=skill("React"), candidate=source_candidate)

    resolved = ResolvedGitHubSkillCandidate(
        skill=skill("React"),
        candidate=source_candidate,
        rule_id=source_candidate.rule_id,
    )
    with pytest.raises(FrozenInstanceError):
        resolved.rule_id = "gh_rule.package.changed.v1"  # type: ignore[misc]


def test_unknown_skills_are_skipped_without_error(monkeypatch) -> None:
    monkeypatch.setattr(github_skill_resolution, "resolve_skill", Mock(return_value=None))

    assert resolve_github_skill_candidates(Mock(), (candidate("Unknown"),)) == ()


def test_same_target_candidates_preserve_distinct_source_signals(monkeypatch) -> None:
    resolver = Mock(return_value=skill("React"))
    monkeypatch.setattr(github_skill_resolution, "resolve_skill", resolver)
    session = Mock()

    result = resolve_github_skill_candidates(
        session,
        (
            candidate("React", "z/package.json", "gh_rule.package.react.v1"),
            candidate(
                "React",
                "a/package.json",
                "gh_rule.package.preact.v1",
                dependency="preact",
            ),
        ),
    )

    assert [item.candidate.source_dependency for item in result] == ["preact", "react"]
    assert [item.rule_id for item in result] == [
        "gh_rule.package.preact.v1",
        "gh_rule.package.react.v1",
    ]
    assert [item.candidate for item in result] == [
        candidate(
            "React",
            "a/package.json",
            "gh_rule.package.preact.v1",
            dependency="preact",
        ),
        candidate("React", "z/package.json", "gh_rule.package.react.v1"),
    ]
    assert resolver.call_count == 2


def test_same_skill_candidates_preserve_each_rule_id_and_manifest(monkeypatch) -> None:
    react = skill("React")
    monkeypatch.setattr(github_skill_resolution, "resolve_skill", Mock(return_value=react))

    result = resolve_github_skill_candidates(
        Mock(),
        (
            candidate("React", "a/package.json", "gh_rule.package.react.v1"),
            candidate("React", "z/package.json", "gh_rule.package.preact.v1"),
        ),
    )

    assert [item.rule_id for item in result] == [
        "gh_rule.package.react.v1",
        "gh_rule.package.preact.v1",
    ]
    assert [item.candidate.source_manifest for item in result] == [
        "a/package.json",
        "z/package.json",
    ]


def test_multiple_candidates_have_deterministic_order(monkeypatch) -> None:
    skills = {"React": skill("React"), "Requests": skill("Requests")}
    monkeypatch.setattr(
        github_skill_resolution, "resolve_skill", lambda _session, name: skills[name]
    )
    session = Mock()

    first = resolve_github_skill_candidates(session, (candidate("Requests"), candidate("React")))
    second = resolve_github_skill_candidates(session, (candidate("React"), candidate("Requests")))

    assert first == second
    assert [item.candidate.target_skill_name for item in first] == ["React", "Requests"]


def test_same_skill_source_signal_order_is_independent_of_input_order(monkeypatch) -> None:
    react = skill("React")
    monkeypatch.setattr(github_skill_resolution, "resolve_skill", lambda _session, _name: react)
    candidates = (
        candidate("React", "z/package.json", "gh_rule.package.react.v1"),
        candidate("React", "a/package.json", "gh_rule.package.preact.v1", dependency="preact"),
    )

    first = resolve_github_skill_candidates(Mock(), candidates)
    second = resolve_github_skill_candidates(Mock(), tuple(reversed(candidates)))

    assert first == second
    assert [item.candidate.source_manifest for item in first] == [
        "a/package.json",
        "z/package.json",
    ]


def test_extractor_signals_are_preserved_by_resolution(monkeypatch) -> None:
    rules = (
        GitHubDeterministicSkillRule(
            rule_id="gh_rule.package.react.v1",
            signal_type=DEPENDENCY_MANIFEST_SIGNAL_TYPE,
            manifest_kind="package_json",
            ecosystem="npm",
            normalized_match_value="react",
            target_skill_name="React",
        ),
        GitHubDeterministicSkillRule(
            rule_id="gh_rule.package.preact.v1",
            signal_type=DEPENDENCY_MANIFEST_SIGNAL_TYPE,
            manifest_kind="package_json",
            ecosystem="npm",
            normalized_match_value="preact",
            target_skill_name="React",
        ),
    )
    snapshot = GitHubRepositorySnapshot(
        canonical_url="https://github.com/demo-user/demo-api",
        repository_name="demo-api",
        owner="demo-user",
        description=None,
        default_branch="main",
        is_public=True,
        is_archived=False,
        languages=(),
        file_tree=(),
        readme_text=None,
        manifest_paths=("a/package.json", "z/package.json"),
        is_demo=True,
        normalized_manifests=(
            GitHubNormalizedManifest(
                path="z/package.json",
                kind="package_json",
                ecosystem="npm",
                dependencies=(GitHubNormalizedDependency(name="react", section=None, metadata={}),),
            ),
            GitHubNormalizedManifest(
                path="a/package.json",
                kind="package_json",
                ecosystem="npm",
                dependencies=(
                    GitHubNormalizedDependency(name="preact", section=None, metadata={}),
                ),
            ),
        ),
    )
    react = skill("React")
    monkeypatch.setattr(github_skill_resolution, "resolve_skill", lambda _session, _name: react)

    candidates = extract_github_skill_candidates(snapshot, rules=rules)
    resolved = resolve_github_skill_candidates(Mock(), candidates)

    assert [item.candidate for item in resolved] == list(candidates)
    assert all(item.candidate is source for item, source in zip(resolved, candidates, strict=True))
    assert [item.rule_id for item in resolved] == [
        "gh_rule.package.preact.v1",
        "gh_rule.package.react.v1",
    ]
