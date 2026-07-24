import re

from app.services.signal_summaries import PUBLIC_CATEGORY_ORDER
from app.services.skill_gap_suggestions import (
    CAPABILITY_CI,
    CAPABILITY_CONFIGURATION,
    CAPABILITY_CONTAINER_ARTIFACT,
    CAPABILITY_DEPENDENCY_RULE,
    CAPABILITY_SOURCE_CODE,
    CAPABILITY_TEST_REMAP,
    _code_rule_capabilities,
    evidence_suggestion_categories,
    public_categories_from_capabilities,
)
from app.utils.github_code_usage_rules import GitHubCodeUsageRule


def _ordered(*categories: str) -> tuple[str, ...]:
    """Expected categories, independently re-derived from the public order."""
    wanted = set(categories)
    return tuple(category for category in PUBLIC_CATEGORY_ORDER if category in wanted)


def test_source_import_rule_yields_resume_source_and_test_usage() -> None:
    # React declares imports and API calls over JS/TS extensions only.
    assert evidence_suggestion_categories("React") == _ordered(
        "resume_evidence", "source_code_usage", "test_usage"
    )


def test_multiple_source_detector_slots_collapse_to_one_category() -> None:
    rule = GitHubCodeUsageRule(
        "Synthetic",
        frozenset({".py"}),
        imports=(re.compile(r"secret_import_pattern"),),
        api_calls=(re.compile(r"secret_api_call_pattern"),),
        class_or_function_usage=(re.compile(r"SecretClass"),),
    )
    categories = public_categories_from_capabilities(_code_rule_capabilities(rule))
    assert categories.count("source_code_usage") == 1
    assert categories == _ordered("source_code_usage", "test_usage")


def test_config_capability_maps_to_application_configuration() -> None:
    assert public_categories_from_capabilities({CAPABILITY_CONFIGURATION}) == (
        "application_configuration",
    )


def test_dependency_capability_maps_to_project_dependencies() -> None:
    # The production dependency registry is intentionally empty; the mapping is
    # verified at the capability layer instead of inventing a production rule.
    assert public_categories_from_capabilities({CAPABILITY_DEPENDENCY_RULE}) == (
        "project_dependencies",
    )


def test_source_and_config_capabilities_use_fixed_order() -> None:
    # Pytest declares source patterns, a config file, and CI patterns.
    assert evidence_suggestion_categories("Pytest") == (
        "resume_evidence",
        "source_code_usage",
        "test_usage",
        "application_configuration",
        "ci_cd_configuration",
    )


def test_config_patterns_without_config_files_do_not_promise_configuration() -> None:
    # PostgreSQL has config_patterns but no config_files, so the extractor can
    # never emit a configuration signal for it.
    assert evidence_suggestion_categories("PostgreSQL") == _ordered(
        "resume_evidence", "source_code_usage", "test_usage", "ci_cd_configuration"
    )


def test_docker_special_case_returns_only_confirmed_categories() -> None:
    assert evidence_suggestion_categories("Docker") == (
        "resume_evidence",
        "container_configuration",
        "ci_cd_configuration",
    )


def test_github_actions_special_case_returns_ci_cd_configuration() -> None:
    assert evidence_suggestion_categories("GitHub Actions") == (
        "resume_evidence",
        "ci_cd_configuration",
    )


def test_container_configuration_is_not_offered_to_other_skills() -> None:
    for skill_name in ("React", "Pytest", "TypeScript", "PostgreSQL"):
        assert "container_configuration" not in evidence_suggestion_categories(skill_name)


def test_skill_without_github_rules_gets_resume_evidence_only() -> None:
    assert evidence_suggestion_categories("C#") == ("resume_evidence",)


def test_unknown_capability_is_ignored_without_leaking_its_name() -> None:
    categories = public_categories_from_capabilities(
        {"future_unknown_detector", CAPABILITY_SOURCE_CODE}
    )
    assert categories == ("source_code_usage",)
    assert "unknown" not in categories
    assert "future_unknown_detector" not in categories


def test_duplicate_capabilities_are_deduplicated() -> None:
    categories = public_categories_from_capabilities(
        {CAPABILITY_SOURCE_CODE, CAPABILITY_TEST_REMAP, CAPABILITY_CONFIGURATION}
    )
    assert len(categories) == len(set(categories))
    assert categories == ("source_code_usage", "test_usage", "application_configuration")


def test_all_capabilities_follow_public_category_order() -> None:
    categories = public_categories_from_capabilities(
        {
            CAPABILITY_DEPENDENCY_RULE,
            CAPABILITY_SOURCE_CODE,
            CAPABILITY_TEST_REMAP,
            CAPABILITY_CONFIGURATION,
            CAPABILITY_CONTAINER_ARTIFACT,
            CAPABILITY_CI,
        }
    )
    assert categories == (
        "project_dependencies",
        "source_code_usage",
        "test_usage",
        "application_configuration",
        "container_configuration",
        "ci_cd_configuration",
    )


def test_categories_are_drawn_from_the_shared_public_vocabulary() -> None:
    for skill_name in ("React", "Pytest", "Docker", "GitHub Actions", "C#", "TypeScript"):
        for category in evidence_suggestion_categories(skill_name):
            assert category in PUBLIC_CATEGORY_ORDER


def test_rule_metadata_never_reaches_the_returned_categories() -> None:
    rule = GitHubCodeUsageRule(
        "Synthetic",
        frozenset({".py", ".tsx"}),
        imports=(re.compile(r"\bimport\s+secretpkg\b"),),
        api_calls=(re.compile(r"\bSecretClient\s*\("),),
        class_or_function_usage=(re.compile(r"\bsecret_function\b"),),
        config_files=(re.compile(r"(?:^|/)secret\.config\.json$"),),
        config_patterns=(re.compile(r"secret://"),),
        ci_patterns=(re.compile(r"\bsecret-ci-job\b"),),
    )
    serialized = str(public_categories_from_capabilities(_code_rule_capabilities(rule)))
    for forbidden in (
        "secretpkg",
        "SecretClient",
        "secret_function",
        "secret.config.json",
        "secret://",
        "secret-ci-job",
        ".py",
        ".tsx",
        "import",
        "api_call",
        "pattern",
        "regex",
        "extension",
        "rule_id",
        "dependency_rule",
        "container_artifact",
    ):
        assert forbidden not in serialized


def test_unmatched_and_empty_lookups_do_not_break_the_helper() -> None:
    assert evidence_suggestion_categories("Totally Unknown Skill") == ("resume_evidence",)
    assert evidence_suggestion_categories("") == ("resume_evidence",)
    assert evidence_suggestion_categories("docker") == ("resume_evidence",)
    assert public_categories_from_capabilities(set()) == ()
    assert public_categories_from_capabilities(frozenset()) == ()


def test_rule_without_extensions_offers_no_source_categories() -> None:
    rule = GitHubCodeUsageRule("Synthetic", frozenset())
    assert _code_rule_capabilities(rule) == frozenset()
    assert public_categories_from_capabilities(_code_rule_capabilities(rule)) == ()
