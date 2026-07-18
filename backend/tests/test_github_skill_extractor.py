from dataclasses import FrozenInstanceError, replace

import pytest

from app.integrations.github import GitHubRepositorySnapshot
from app.utils.github_manifests import (
    GitHubManifestWarning,
    GitHubNormalizedDependency,
    GitHubNormalizedManifest,
)
from app.utils.github_skill_extractor import (
    GitHubSkillCandidate,
    extract_github_skill_candidates,
)
from app.utils.github_skill_rules import (
    DEPENDENCY_MANIFEST_SIGNAL_TYPE,
    GitHubDeterministicSkillRule,
)


RULES = (
    GitHubDeterministicSkillRule(
        rule_id="gh_rule.package.react.v1",
        signal_type=DEPENDENCY_MANIFEST_SIGNAL_TYPE,
        manifest_kind="package_json",
        ecosystem="npm",
        normalized_match_value="react",
        target_skill_name="React",
    ),
    GitHubDeterministicSkillRule(
        rule_id="gh_rule.python.requests.v1",
        signal_type=DEPENDENCY_MANIFEST_SIGNAL_TYPE,
        manifest_kind="requirements_txt",
        ecosystem="python",
        normalized_match_value="requests",
        target_skill_name="Requests",
    ),
)


def make_snapshot(
    manifests: tuple[GitHubNormalizedManifest, ...],
) -> GitHubRepositorySnapshot:
    return GitHubRepositorySnapshot(
        canonical_url="https://github.com/demo-user/demo-api",
        repository_name="demo-api",
        owner="demo-user",
        description=None,
        default_branch="main",
        is_public=True,
        is_archived=False,
        languages=("Python",),
        file_tree=("package.json",),
        readme_text="ignored",
        manifest_paths=tuple(manifest.path for manifest in manifests),
        is_demo=True,
        normalized_manifests=manifests,
    )


def manifest(path: str, kind: str, ecosystem: str, *dependencies: str) -> GitHubNormalizedManifest:
    return GitHubNormalizedManifest(
        path=path,
        kind=kind,
        ecosystem=ecosystem,
        dependencies=tuple(
            GitHubNormalizedDependency(name=name, section=None, metadata={})
            for name in dependencies
        ),
    )


def test_one_dependency_creates_one_rule_backed_candidate() -> None:
    snapshot = make_snapshot((manifest("package.json", "package_json", "npm", "react"),))

    candidates = extract_github_skill_candidates(snapshot, rules=RULES)

    assert len(candidates) == 1
    assert candidates[0].target_skill_name == "React"
    assert candidates[0].source_dependency == "react"
    assert candidates[0].rule_id == "gh_rule.package.react.v1"


def test_candidate_requires_rule_id_and_is_immutable() -> None:
    with pytest.raises(TypeError):
        GitHubSkillCandidate(
            target_skill_name="React",
            source_dependency="react",
            source_manifest="package.json",
            manifest_kind="package_json",
            ecosystem="npm",
            signal_type=DEPENDENCY_MANIFEST_SIGNAL_TYPE,
        )

    candidate = extract_github_skill_candidates(
        make_snapshot((manifest("package.json", "package_json", "npm", "react"),)),
        rules=RULES,
    )[0]
    with pytest.raises(FrozenInstanceError):
        candidate.rule_id = "gh_rule.package.changed.v1"  # type: ignore[misc]


def test_duplicate_dependencies_and_manifests_deduplicate_to_one_candidate() -> None:
    snapshot = make_snapshot(
        (
            manifest("z/package.json", "package_json", "npm", "react", "react"),
            manifest("a/package.json", "package_json", "npm", "react"),
        )
    )

    candidates = extract_github_skill_candidates(snapshot, rules=RULES)

    assert len(candidates) == 1
    assert candidates[0].source_manifest == "a/package.json"


def test_same_target_rules_preserve_their_matched_rule_ids_without_affecting_deduplication() -> (
    None
):
    react = RULES[0]
    preact = GitHubDeterministicSkillRule(
        rule_id="gh_rule.package.preact.v1",
        signal_type=DEPENDENCY_MANIFEST_SIGNAL_TYPE,
        manifest_kind="package_json",
        ecosystem="npm",
        normalized_match_value="preact",
        target_skill_name="React",
    )

    react_candidate = extract_github_skill_candidates(
        make_snapshot((manifest("package.json", "package_json", "npm", "react"),)),
        rules=(react, preact),
    )
    preact_candidate = extract_github_skill_candidates(
        make_snapshot((manifest("package.json", "package_json", "npm", "preact"),)),
        rules=(react, preact),
    )
    deduplicated = extract_github_skill_candidates(
        make_snapshot(
            (
                manifest("z/package.json", "package_json", "npm", "react"),
                manifest("a/package.json", "package_json", "npm", "preact"),
            )
        ),
        rules=(react, preact),
    )

    assert react_candidate[0].rule_id == react.rule_id
    assert preact_candidate[0].rule_id == preact.rule_id
    assert len(deduplicated) == 1
    assert deduplicated[0].source_manifest == "a/package.json"
    assert deduplicated[0].rule_id == preact.rule_id


def test_unknown_dependency_and_empty_registry_produce_no_candidates() -> None:
    snapshot = make_snapshot((manifest("package.json", "package_json", "npm", "unknown"),))

    assert extract_github_skill_candidates(snapshot, rules=RULES) == ()
    assert extract_github_skill_candidates(snapshot, rules=()) == ()


def test_result_order_and_result_are_independent_of_input_order() -> None:
    manifests = (
        manifest("z/requirements.txt", "requirements_txt", "python", "requests"),
        manifest("a/package.json", "package_json", "npm", "react"),
    )

    first = extract_github_skill_candidates(make_snapshot(manifests), rules=RULES)
    second = extract_github_skill_candidates(make_snapshot(tuple(reversed(manifests))), rules=RULES)

    assert first == second
    assert [candidate.target_skill_name for candidate in first] == ["React", "Requests"]


def test_extractor_uses_only_normalized_manifests() -> None:
    snapshot = make_snapshot((manifest("package.json", "package_json", "npm", "react"),))
    changed_non_manifest_fields = replace(
        snapshot,
        languages=("Rust",),
        file_tree=("README.md",),
        readme_text="different",
        manifest_warnings=(
            GitHubManifestWarning(
                path="package.json", kind="package_json", code="malformed", detail=None
            ),
        ),
    )

    assert extract_github_skill_candidates(
        snapshot, rules=RULES
    ) == extract_github_skill_candidates(changed_non_manifest_fields, rules=RULES)
