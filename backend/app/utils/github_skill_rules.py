"""Static, exact GitHub dependency-to-skill mapping rules (§17.5)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Iterable

from app.utils.github_manifests import MANIFEST_KINDS


DEPENDENCY_MANIFEST_SIGNAL_TYPE: Final = "dependency_manifest"
_SUPPORTED_MANIFEST_IDENTITIES: Final = frozenset({*MANIFEST_KINDS.values(), ("csproj", "nuget")})


class GitHubSkillRuleValidationError(ValueError):
    """Raised when a static GitHub deterministic rule registry is invalid."""


@dataclass(frozen=True, slots=True, order=True)
class GitHubDeterministicSkillRule:
    """One explicit dependency-manifest mapping to a canonical target skill name."""

    signal_type: str
    manifest_kind: str
    ecosystem: str
    normalized_match_value: str
    target_skill_name: str

    def __post_init__(self) -> None:
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
    ordered = tuple(sorted(rules))
    targets_by_key: dict[tuple[str, str, str, str], str] = {}
    for rule in ordered:
        key = _lookup_key(
            signal_type=rule.signal_type,
            manifest_kind=rule.manifest_kind,
            ecosystem=rule.ecosystem,
            normalized_match_value=rule.normalized_match_value,
        )
        previous_target = targets_by_key.get(key)
        if previous_target is not None:
            if previous_target != rule.target_skill_name:
                raise GitHubSkillRuleValidationError("GitHub rule registry has a conflict")
            raise GitHubSkillRuleValidationError("GitHub rule registry has a duplicate")
        targets_by_key[key] = rule.target_skill_name
    return ordered


# §17.5 defines the rule mechanism but approves no concrete production mappings.
GITHUB_DETERMINISTIC_SKILL_RULES: Final[tuple[GitHubDeterministicSkillRule, ...]] = (
    validate_github_skill_rules(())
)


def match_github_skill_rule(
    *,
    signal_type: str,
    manifest_kind: str,
    ecosystem: str,
    normalized_match_value: str,
    rules: tuple[GitHubDeterministicSkillRule, ...] = GITHUB_DETERMINISTIC_SKILL_RULES,
) -> GitHubDeterministicSkillRule | None:
    """Return a rule only for an exact, already-normalized signal identity."""
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
