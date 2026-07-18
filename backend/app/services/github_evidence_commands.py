"""Pure construction of canonical GitHub deterministic evidence commands."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType
from typing import Final, Mapping, Sequence
from uuid import UUID

from app.models.evidence_unit import EvidenceUnit
from app.services.evidence_skill_links import EvidenceSkillLinkCandidateMismatchError
from app.services.github_skill_resolution import ResolvedGitHubSkillCandidate


GITHUB_DETERMINISTIC_EXTRACTION_METHOD: Final = "deterministic"
GITHUB_DETERMINISTIC_EXTRACTION_VERSION: Final = "github-deterministic-v1"
GITHUB_DETERMINISTIC_EXTRACTION_CONFIDENCE: Final = Decimal("1.00")
_GITHUB_DETERMINISTIC_EXTRACTOR: Final = "github_deterministic"


@dataclass(frozen=True, slots=True)
class GitHubEvidenceCommand:
    """One desired deterministic EvidenceSkillLink, ready for a later builder."""

    candidate_id: UUID
    evidence_unit_id: UUID
    skill_id: UUID
    extraction_method: str
    extraction_version: str
    extraction_confidence: Decimal
    context: Mapping[str, object]


def build_github_evidence_commands(
    *,
    candidate_id: UUID,
    evidence_unit: EvidenceUnit,
    resolved_candidates: Sequence[ResolvedGitHubSkillCandidate],
) -> tuple[GitHubEvidenceCommand, ...]:
    """Aggregate resolved manifest signals into canonical per-Skill commands."""
    if evidence_unit.candidate_id != candidate_id:
        raise EvidenceSkillLinkCandidateMismatchError(
            "GitHub evidence command candidate_id differs from EvidenceUnit candidate_id"
        )
    grouped: dict[tuple[UUID, UUID, str, str], list[ResolvedGitHubSkillCandidate]] = {}
    for resolved in resolved_candidates:
        key = (
            evidence_unit.id,
            resolved.skill.id,
            GITHUB_DETERMINISTIC_EXTRACTION_METHOD,
            GITHUB_DETERMINISTIC_EXTRACTION_VERSION,
        )
        grouped.setdefault(key, []).append(resolved)

    commands = [
        _build_command(
            candidate_id=candidate_id,
            evidence_unit_id=evidence_unit_id,
            skill_id=skill_id,
            resolved_candidates=group,
        )
        for (evidence_unit_id, skill_id, _method, _version), group in grouped.items()
    ]
    return tuple(sorted(commands, key=lambda command: _command_key(command, grouped)))


def _build_command(
    *,
    candidate_id: UUID,
    evidence_unit_id: UUID,
    skill_id: UUID,
    resolved_candidates: Sequence[ResolvedGitHubSkillCandidate],
) -> GitHubEvidenceCommand:
    signals_by_identity: dict[tuple[str, str, str, str, str, str], Mapping[str, str]] = {}
    for resolved in resolved_candidates:
        candidate = resolved.candidate
        signal = MappingProxyType(
            {
                "type": candidate.signal_type,
                "manifest": candidate.source_manifest,
                "manifest_kind": candidate.manifest_kind,
                "ecosystem": candidate.ecosystem,
                "matched_value": candidate.source_dependency,
                "rule_id": candidate.rule_id,
            }
        )
        signals_by_identity.setdefault(_signal_identity(signal), signal)

    signals = tuple(sorted(signals_by_identity.values(), key=_signal_key))
    context = MappingProxyType(
        {
            "extractor": _GITHUB_DETERMINISTIC_EXTRACTOR,
            "version": GITHUB_DETERMINISTIC_EXTRACTION_VERSION,
            "signals": signals,
        }
    )
    return GitHubEvidenceCommand(
        candidate_id=candidate_id,
        evidence_unit_id=evidence_unit_id,
        skill_id=skill_id,
        extraction_method=GITHUB_DETERMINISTIC_EXTRACTION_METHOD,
        extraction_version=GITHUB_DETERMINISTIC_EXTRACTION_VERSION,
        extraction_confidence=GITHUB_DETERMINISTIC_EXTRACTION_CONFIDENCE,
        context=context,
    )


def _signal_identity(signal: Mapping[str, str]) -> tuple[str, str, str, str, str, str]:
    return (
        signal["type"],
        signal["manifest"],
        signal["manifest_kind"],
        signal["ecosystem"],
        signal["matched_value"],
        signal["rule_id"],
    )


def _signal_key(signal: Mapping[str, str]) -> tuple[str, str, str, str, str]:
    return (
        signal["type"],
        signal["manifest"],
        signal["ecosystem"],
        signal["matched_value"],
        signal["rule_id"],
    )


def _command_key(
    command: GitHubEvidenceCommand,
    grouped: Mapping[tuple[UUID, UUID, str, str], Sequence[ResolvedGitHubSkillCandidate]],
) -> tuple[str, str]:
    group = grouped[
        (
            command.evidence_unit_id,
            command.skill_id,
            command.extraction_method,
            command.extraction_version,
        )
    ]
    return group[0].skill.normalized_name, str(command.skill_id)
