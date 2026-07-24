"""Deterministic evidence suggestions for skills missing from a Skill Passport.

Pure in-memory inspection of the static extraction registries: no Session, no
Pydantic, no candidate data, no extractor execution. A suggestion only states
that a public evidence category *could* confirm the skill with an extractor that
already exists — never that the candidate lacks the skill.
"""

from __future__ import annotations

from app.services.signal_summaries import (
    PUBLIC_CATEGORY_ORDER,
    RESUME_EVIDENCE_CATEGORY,
)
from app.utils.github_code_usage_rules import (
    GITHUB_CODE_USAGE_RULES,
    GitHubCodeUsageRule,
)
from app.utils.github_skill_rules import GITHUB_DETERMINISTIC_SKILL_RULES

# Internal rule capabilities. Never serialized; only mapped to public categories.
CAPABILITY_DEPENDENCY_RULE = "dependency_rule"
CAPABILITY_SOURCE_CODE = "source_code"
CAPABILITY_TEST_REMAP = "test_remap"
CAPABILITY_CONFIGURATION = "configuration"
CAPABILITY_CONTAINER_ARTIFACT = "container_artifact"
CAPABILITY_CI = "ci"

_CAPABILITY_TO_CATEGORY: dict[str, str] = {
    CAPABILITY_DEPENDENCY_RULE: "project_dependencies",
    CAPABILITY_SOURCE_CODE: "source_code_usage",
    CAPABILITY_TEST_REMAP: "test_usage",
    CAPABILITY_CONFIGURATION: "application_configuration",
    CAPABILITY_CONTAINER_ARTIFACT: "container_configuration",
    CAPABILITY_CI: "ci_cd_configuration",
}

# Canonical ontology names served by the hardcoded detectors in
# github_skill_extractor. Docker also receives the docker-in-CI attribution.
_HARDCODED_DETECTOR_CAPABILITIES: dict[str, frozenset[str]] = {
    "Docker": frozenset({CAPABILITY_CONTAINER_ARTIFACT, CAPABILITY_CI}),
    "GitHub Actions": frozenset({CAPABILITY_CI}),
}


def _code_rule_capabilities(rule: GitHubCodeUsageRule) -> frozenset[str]:
    """Inspect which supported detectors a source rule actually declares."""
    capabilities: set[str] = set()
    # Pattern detectors need a matching extension; extension-only rules emit a
    # source signal on their own. Either way the source path requires extensions.
    if rule.extensions:
        capabilities.add(CAPABILITY_SOURCE_CODE)
        # The extractor remaps every source signal to test usage on test paths.
        capabilities.add(CAPABILITY_TEST_REMAP)
    # Configuration signals require a config file matcher; patterns alone never fire.
    if rule.config_files:
        capabilities.add(CAPABILITY_CONFIGURATION)
    if rule.ci_patterns:
        capabilities.add(CAPABILITY_CI)
    return frozenset(capabilities)


def _build_capability_index() -> dict[str, frozenset[str]]:
    index: dict[str, set[str]] = {}
    for dependency_rule in GITHUB_DETERMINISTIC_SKILL_RULES:
        index.setdefault(dependency_rule.target_skill_name, set()).add(CAPABILITY_DEPENDENCY_RULE)
    for code_rule in GITHUB_CODE_USAGE_RULES:
        index.setdefault(code_rule.target_skill_name, set()).update(
            _code_rule_capabilities(code_rule)
        )
    for skill_name, capabilities in _HARDCODED_DETECTOR_CAPABILITIES.items():
        index.setdefault(skill_name, set()).update(capabilities)
    return {name: frozenset(capabilities) for name, capabilities in index.items()}


# Registries are static after import, so one immutable index is enough.
_CAPABILITIES_BY_SKILL_NAME: dict[str, frozenset[str]] = _build_capability_index()


def public_categories_from_capabilities(capabilities: frozenset[str] | set[str]) -> tuple[str, ...]:
    """Map internal rule capabilities to deduplicated, ordered public categories."""
    found: set[str] = set()
    for capability in capabilities:
        category = _CAPABILITY_TO_CATEGORY.get(capability)
        if category is not None:
            found.add(category)
    return tuple(category for category in PUBLIC_CATEGORY_ORDER if category in found)


def evidence_suggestion_categories(skill_name: str) -> tuple[str, ...]:
    """Return ordered public categories that could confirm one ontology skill.

    ``resume_evidence`` is always available because the text extractor covers the
    whole active ontology. Project categories come only from declared rules.
    """
    capabilities = _CAPABILITIES_BY_SKILL_NAME.get(skill_name, frozenset())
    categories = {RESUME_EVIDENCE_CATEGORY, *public_categories_from_capabilities(capabilities)}
    return tuple(category for category in PUBLIC_CATEGORY_ORDER if category in categories)
