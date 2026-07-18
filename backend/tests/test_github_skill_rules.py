from dataclasses import FrozenInstanceError

import pytest

from app.utils.github_skill_rules import (
    DEPENDENCY_MANIFEST_SIGNAL_TYPE,
    GITHUB_DETERMINISTIC_SKILL_RULES,
    GitHubDeterministicSkillRule,
    GitHubSkillRuleValidationError,
    match_github_skill_rule,
    validate_github_skill_rules,
)


def make_rule(target_skill_name: str = "React") -> GitHubDeterministicSkillRule:
    return GitHubDeterministicSkillRule(
        signal_type=DEPENDENCY_MANIFEST_SIGNAL_TYPE,
        manifest_kind="package_json",
        ecosystem="npm",
        normalized_match_value="react",
        target_skill_name=target_skill_name,
    )


def test_exact_match_returns_the_immutable_rule() -> None:
    rule = make_rule()
    registry = validate_github_skill_rules((rule,))

    result = match_github_skill_rule(
        signal_type="dependency_manifest",
        manifest_kind="package_json",
        ecosystem="npm",
        normalized_match_value="react",
        rules=registry,
    )

    assert result is rule
    with pytest.raises(FrozenInstanceError):
        rule.target_skill_name = "Other"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("signal_type", "manifest_kind", "ecosystem", "value"),
    [
        ("dependency_manifest", "package_json", "npm", "reactive"),
        ("dependency_manifest", "go_mod", "go", "react"),
        ("dependency_manifest", "package_json", "node", "react"),
        ("repository_language", "package_json", "npm", "react"),
        ("dependency_manifest", "package_json", "npm", "React"),
    ],
)
def test_lookup_is_exact_and_has_no_fallback_matching(
    signal_type: str, manifest_kind: str, ecosystem: str, value: str
) -> None:
    assert (
        match_github_skill_rule(
            signal_type=signal_type,
            manifest_kind=manifest_kind,
            ecosystem=ecosystem,
            normalized_match_value=value,
            rules=(make_rule(),),
        )
        is None
    )


def test_registry_is_canonically_ordered_and_rejects_duplicate_or_conflict() -> None:
    angular = GitHubDeterministicSkillRule(
        signal_type="dependency_manifest",
        manifest_kind="package_json",
        ecosystem="npm",
        normalized_match_value="angular",
        target_skill_name="Angular",
    )
    react = make_rule()

    assert validate_github_skill_rules((react, angular)) == (angular, react)
    with pytest.raises(GitHubSkillRuleValidationError, match="duplicate"):
        validate_github_skill_rules((react, react))
    with pytest.raises(GitHubSkillRuleValidationError, match="conflict"):
        validate_github_skill_rules((react, make_rule("ReactJS")))


def test_production_registry_is_intentionally_empty() -> None:
    assert GITHUB_DETERMINISTIC_SKILL_RULES == ()
