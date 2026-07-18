"""Static, exact GitHub dependency-to-skill mapping rules (§17.5)."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Final, Iterable

from app.utils.github_manifests import MANIFEST_KINDS


DEPENDENCY_MANIFEST_SIGNAL_TYPE: Final = "dependency_manifest"
_SUPPORTED_MANIFEST_IDENTITIES: Final = frozenset({*MANIFEST_KINDS.values(), ("csproj", "nuget")})
_RULE_ID_PATTERN: Final = re.compile(r"^gh_rule\.[a-z0-9_]+(?:\.[a-z0-9_]+)+\.v[1-9][0-9]*$")
_MAX_RULE_ID_LENGTH: Final = 128


class GitHubSkillRuleValidationError(ValueError):
    """Raised when a static GitHub deterministic rule registry is invalid."""


@dataclass(frozen=True, slots=True)
class GitHubDeterministicSkillRule:
    """One explicit dependency-manifest mapping to a canonical target skill name."""

    rule_id: str
    signal_type: str
    manifest_kind: str
    ecosystem: str
    normalized_match_value: str
    target_skill_name: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.rule_id, str)
            or len(self.rule_id) > _MAX_RULE_ID_LENGTH
            or not _RULE_ID_PATTERN.fullmatch(self.rule_id)
        ):
            raise GitHubSkillRuleValidationError("GitHub rule ID is invalid")
        if self.signal_type != DEPENDENCY_MANIFEST_SIGNAL_TYPE:
            raise GitHubSkillRuleValidationError("GitHub rule signal type is invalid")
        if (self.manifest_kind, self.ecosystem) not in _SUPPORTED_MANIFEST_IDENTITIES:
            raise GitHubSkillRuleValidationError("GitHub rule manifest identity is invalid")
        if not self.normalized_match_value or not self.target_skill_name.strip():
            raise GitHubSkillRuleValidationError("GitHub rule values must be non-empty")


def validate_github_skill_rules(
    rules: Iterable[GitHubDeterministicSkillRule],
) -> tuple[GitHubDeterministicSkillRule, ...]:
    """Return the canonical static registry or fail deterministically on a conflict."""
    ordered = tuple(sorted(rules, key=_canonical_rule_key))
    rules_by_id: dict[str, GitHubDeterministicSkillRule] = {}
    rules_by_key: dict[tuple[str, str, str, str], GitHubDeterministicSkillRule] = {}
    for rule in ordered:
        previous_rule_id = rules_by_id.get(rule.rule_id)
        if previous_rule_id is not None:
            if _contract_fields(previous_rule_id) != _contract_fields(rule):
                raise GitHubSkillRuleValidationError(
                    "GitHub rule ID has conflicting contract fields"
                )
            raise GitHubSkillRuleValidationError("GitHub rule registry has a duplicate rule ID")
        key = _lookup_key(
            signal_type=rule.signal_type,
            manifest_kind=rule.manifest_kind,
            ecosystem=rule.ecosystem,
            normalized_match_value=rule.normalized_match_value,
        )
        previous_rule = rules_by_key.get(key)
        if previous_rule is not None:
            if (
                previous_rule.rule_id != rule.rule_id
                or previous_rule.target_skill_name != rule.target_skill_name
            ):
                raise GitHubSkillRuleValidationError("GitHub rule registry has a lookup conflict")
            raise GitHubSkillRuleValidationError("GitHub rule registry has a duplicate")
        rules_by_id[rule.rule_id] = rule
        rules_by_key[key] = rule
    return ordered


def match_github_skill_rule(
    *,
    signal_type: str,
    manifest_kind: str,
    ecosystem: str,
    normalized_match_value: str,
    rules: tuple[GitHubDeterministicSkillRule, ...] | None = None,
) -> GitHubDeterministicSkillRule | None:
    """Return a rule only for an exact, already-normalized signal identity."""
    if rules is None:
        rules = GITHUB_DETERMINISTIC_SKILL_RULES
    lookup_key = _lookup_key(
        signal_type=signal_type,
        manifest_kind=manifest_kind,
        ecosystem=ecosystem,
        normalized_match_value=normalized_match_value,
    )
    for rule in rules:
        if (
            _lookup_key(
                signal_type=rule.signal_type,
                manifest_kind=rule.manifest_kind,
                ecosystem=rule.ecosystem,
                normalized_match_value=rule.normalized_match_value,
            )
            == lookup_key
        ):
            return rule
    return None


def _lookup_key(
    *,
    signal_type: str,
    manifest_kind: str,
    ecosystem: str,
    normalized_match_value: str,
) -> tuple[str, str, str, str]:
    return signal_type, manifest_kind, ecosystem, normalized_match_value


def _canonical_rule_key(rule: GitHubDeterministicSkillRule) -> tuple[str, str, str, str, str]:
    return (
        rule.signal_type,
        rule.manifest_kind,
        rule.ecosystem,
        rule.normalized_match_value,
        rule.target_skill_name,
    )


def _contract_fields(rule: GitHubDeterministicSkillRule) -> tuple[str, str, str, str, str]:
    return _canonical_rule_key(rule)


# §17.5 defines the rule mechanism but approves no concrete production mappings.
GITHUB_DETERMINISTIC_SKILL_RULES: Final[tuple[GitHubDeterministicSkillRule, ...]] = (
    validate_github_skill_rules(())
)
