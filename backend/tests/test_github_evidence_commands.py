from dataclasses import FrozenInstanceError
from types import MappingProxyType
from uuid import UUID, uuid4

import pytest

from app.models.evidence_unit import EvidenceUnit
from app.models.skill import Skill
from app.services.evidence_skill_links import EvidenceSkillLinkCandidateMismatchError
from app.services.github_evidence_commands import (
    GITHUB_DETERMINISTIC_EXTRACTION_CONFIDENCE,
    GITHUB_DETERMINISTIC_EXTRACTION_METHOD,
    GITHUB_DETERMINISTIC_EXTRACTION_VERSION,
    build_github_evidence_commands,
)
from app.services.github_skill_resolution import ResolvedGitHubSkillCandidate
from app.utils.github_skill_extractor import GitHubSkillCandidate


def make_skill(name: str, skill_id: UUID) -> Skill:
    return Skill(
        id=skill_id,
        canonical_name=name,
        normalized_name=name.lower(),
        category="framework",
        ontology_version="v1",
    )


def make_resolved(
    skill: Skill,
    *,
    manifest: str,
    dependency: str,
    rule_id: str,
) -> ResolvedGitHubSkillCandidate:
    candidate = GitHubSkillCandidate(
        target_skill_name=skill.canonical_name,
        source_dependency=dependency,
        source_manifest=manifest,
        manifest_kind="package_json",
        ecosystem="npm",
        signal_type="dependency_manifest",
        rule_id=rule_id,
    )
    return ResolvedGitHubSkillCandidate(skill=skill, candidate=candidate, rule_id=rule_id)


def make_evidence(evidence_unit_id: UUID, candidate_id: UUID) -> EvidenceUnit:
    return EvidenceUnit(
        id=evidence_unit_id,
        candidate_id=candidate_id,
        source_type="github_repository",
    )


def test_one_skill_creates_one_immutable_canonical_command() -> None:
    candidate_id = uuid4()
    evidence = make_evidence(uuid4(), candidate_id)
    react = make_skill("React", uuid4())

    command = build_github_evidence_commands(
        candidate_id=candidate_id,
        evidence_unit=evidence,
        resolved_candidates=(
            make_resolved(
                react,
                manifest="package.json",
                dependency="react",
                rule_id="gh_rule.package.react.v1",
            ),
        ),
    )[0]

    assert command.candidate_id == candidate_id
    assert command.evidence_unit_id == evidence.id
    assert command.skill_id == react.id
    assert command.extraction_method == GITHUB_DETERMINISTIC_EXTRACTION_METHOD
    assert command.extraction_version == GITHUB_DETERMINISTIC_EXTRACTION_VERSION
    assert command.extraction_confidence == GITHUB_DETERMINISTIC_EXTRACTION_CONFIDENCE
    assert command.context == {
        "extractor": "github_deterministic",
        "version": "github-deterministic-v1",
        "signals": (
            {
                "type": "dependency_manifest",
                "manifest": "package.json",
                "manifest_kind": "package_json",
                "ecosystem": "npm",
                "matched_value": "react",
                "rule_id": "gh_rule.package.react.v1",
            },
        ),
    }
    with pytest.raises(FrozenInstanceError):
        command.skill_id = uuid4()  # type: ignore[misc]
    with pytest.raises(TypeError):
        command.context["version"] = "changed"  # type: ignore[index]
    with pytest.raises(AttributeError):
        command.context["signals"].append({})  # type: ignore[union-attr]
    with pytest.raises(TypeError):
        command.context["signals"][0]["rule_id"] = "changed"  # type: ignore[index]


def test_signals_are_aggregated_deduplicated_and_canonically_sorted() -> None:
    candidate_id = uuid4()
    evidence = make_evidence(uuid4(), candidate_id)
    react = make_skill("React", uuid4())
    preact = make_resolved(
        react,
        manifest="a/package.json",
        dependency="preact",
        rule_id="gh_rule.package.preact.v1",
    )
    react_signal = make_resolved(
        react,
        manifest="z/package.json",
        dependency="react",
        rule_id="gh_rule.package.react.v1",
    )

    commands = build_github_evidence_commands(
        candidate_id=candidate_id,
        evidence_unit=evidence,
        resolved_candidates=(react_signal, preact, preact),
    )

    assert len(commands) == 1
    assert tuple(commands[0].context["signals"]) == (
        MappingProxyType(
            {
                "type": "dependency_manifest",
                "manifest": "a/package.json",
                "manifest_kind": "package_json",
                "ecosystem": "npm",
                "matched_value": "preact",
                "rule_id": "gh_rule.package.preact.v1",
            }
        ),
        MappingProxyType(
            {
                "type": "dependency_manifest",
                "manifest": "z/package.json",
                "manifest_kind": "package_json",
                "ecosystem": "npm",
                "matched_value": "react",
                "rule_id": "gh_rule.package.react.v1",
            }
        ),
    )


def test_commands_are_grouped_and_sorted_by_skill_normalized_name_then_id() -> None:
    candidate_id = uuid4()
    evidence = make_evidence(uuid4(), candidate_id)
    react = make_skill("React", UUID("00000000-0000-0000-0000-000000000002"))
    angular = make_skill("Angular", UUID("00000000-0000-0000-0000-000000000001"))

    commands = build_github_evidence_commands(
        candidate_id=candidate_id,
        evidence_unit=evidence,
        resolved_candidates=(
            make_resolved(
                react,
                manifest="package.json",
                dependency="react",
                rule_id="gh_rule.package.react.v1",
            ),
            make_resolved(
                angular,
                manifest="package.json",
                dependency="angular",
                rule_id="gh_rule.package.angular.v1",
            ),
        ),
    )

    assert [command.skill_id for command in commands] == [angular.id, react.id]


def test_ids_come_only_from_factory_arguments_and_commands_are_deterministic() -> None:
    argument_candidate_id = uuid4()
    evidence = make_evidence(uuid4(), argument_candidate_id)
    react = make_skill("React", uuid4())
    resolved = (
        make_resolved(
            react,
            manifest="z/package.json",
            dependency="react",
            rule_id="gh_rule.package.react.v1",
        ),
        make_resolved(
            react,
            manifest="a/package.json",
            dependency="preact",
            rule_id="gh_rule.package.preact.v1",
        ),
    )

    first = build_github_evidence_commands(
        candidate_id=argument_candidate_id,
        evidence_unit=evidence,
        resolved_candidates=resolved,
    )
    second = build_github_evidence_commands(
        candidate_id=argument_candidate_id,
        evidence_unit=evidence,
        resolved_candidates=tuple(reversed(resolved)),
    )

    assert first == second
    assert first[0].candidate_id == argument_candidate_id
    assert first[0].evidence_unit_id == evidence.id
    assert first[0].context["signals"][0]["rule_id"] == "gh_rule.package.preact.v1"


def test_factory_rejects_candidate_and_evidence_unit_mismatch() -> None:
    candidate_id = uuid4()
    evidence = make_evidence(uuid4(), uuid4())

    with pytest.raises(
        EvidenceSkillLinkCandidateMismatchError,
        match="GitHub evidence command candidate_id differs from EvidenceUnit candidate_id",
    ):
        build_github_evidence_commands(
            candidate_id=candidate_id,
            evidence_unit=evidence,
            resolved_candidates=(),
        )
