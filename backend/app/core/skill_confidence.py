"""Tunable, deterministic parameters for Skill Passport confidence."""

from __future__ import annotations

# The weights intentionally add up to one. GitHub confidence is capped below
# 100% because repository evidence is useful evidence, not proof of mastery.
SOURCE_USAGE_WEIGHT = 0.40
EVIDENCE_DIVERSITY_WEIGHT = 0.20
PROJECT_COVERAGE_WEIGHT = 0.20
CROSS_REPOSITORY_WEIGHT = 0.10
REPOSITORY_QUALITY_WEIGHT = 0.10

GITHUB_CONFIDENCE_CAP_PERCENT = 95

# Saturation parameters prevent a large repository from inflating a score indefinitely.
DIVERSITY_SATURATION_TYPES = 3.0
COVERAGE_SATURATION_PATHS = 12
CROSS_REPOSITORY_SATURATION_REPOSITORIES = 2.0
QUALITY_SATURATION_ARTIFACTS = 3.0

# These values describe the evidentiary strength of a single observed signal,
# not a candidate's proficiency. Future deterministic extractors can emit the
# strong types without changing the calculator.
SOURCE_USAGE_SIGNAL_STRENGTHS = {
    "source_api_call": 0.95,
    "source_logic": 0.90,
    "source_class_usage": 0.80,
    "source_function_usage": 0.75,
    "source_import": 0.70,
    "test_usage": 0.60,
    "configuration_usage": 0.30,
    "docker": 0.30,
    "ci": 0.25,
    "dependency_manifest": 0.12,
    "package_manifest": 0.12,
    "readme": 0.05,
    "lockfile": 0.02,
}

WEAK_SIGNAL_TYPES = frozenset(
    {"dependency_manifest", "package_manifest", "readme", "lockfile"}
)
