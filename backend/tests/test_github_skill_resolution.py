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


def candidate(
    target: str,
    path: str = "package.json",
    rule_id: str = "gh_rule.package.react.v1",
) -> GitHubSkillCandidate:
    return GitHubSkillCandidate(
        target_skill_name=target,
        source_dependency=target.lower(),
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


def test_duplicate_targets_resolve_once_and_choose_canonical_candidate(monkeypatch) -> None:
    resolver = Mock(return_value=skill("React"))
    monkeypatch.setattr(github_skill_resolution, "resolve_skill", resolver)
    session = Mock()

    result = resolve_github_skill_candidates(
        session,
        (
            candidate("React", "z/package.json", "gh_rule.package.react.v1"),
            candidate("React", "a/package.json", "gh_rule.package.preact.v1"),
        ),
    )

    assert result[0].candidate.source_manifest == "a/package.json"
    assert result[0].rule_id == "gh_rule.package.preact.v1"
    resolver.assert_called_once_with(session, "React")


def test_same_skill_candidates_preserve_each_rule_id_when_resolved_individually(
    monkeypatch,
) -> None:
    react = skill("React")
    monkeypatch.setattr(github_skill_resolution, "resolve_skill", Mock(return_value=react))

    first = resolve_github_skill_candidates(
        Mock(), (candidate("React", rule_id="gh_rule.package.react.v1"),)
    )
    second = resolve_github_skill_candidates(
        Mock(), (candidate("React", rule_id="gh_rule.package.preact.v1"),)
    )

    assert first[0].rule_id == "gh_rule.package.react.v1"
    assert second[0].rule_id == "gh_rule.package.preact.v1"


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
