from dataclasses import FrozenInstanceError
from decimal import Decimal
from inspect import getsource, signature
from types import MappingProxyType
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest

from app.models.evidence_skill_link import EvidenceSkillLink
from app.models.evidence_unit import EvidenceUnit
from app.models.skill import Skill
from app.services.evidence_skill_links import (
    EvidenceSkillLinkCandidateMismatchError,
    EvidenceSkillLinkPersistenceResult,
)
from app.services.github_evidence_skill_link_builder import GitHubEvidenceSkillLinkValues
from app.services.github_evidence_skill_link_orchestration import (
    persist_resolved_github_skill_candidates,
)
from app.services.github_skill_resolution import ResolvedGitHubSkillCandidate
from app.utils.github_skill_extractor import GitHubSkillCandidate
import app.services.github_evidence_skill_link_orchestration as orchestration_module


def make_evidence(evidence_unit_id: UUID, candidate_id: UUID) -> EvidenceUnit:
    return EvidenceUnit(
        id=evidence_unit_id,
        candidate_id=candidate_id,
        source_type="github_repository",
    )


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


def persistence_result(*, created: bool, changed: bool) -> EvidenceSkillLinkPersistenceResult:
    return EvidenceSkillLinkPersistenceResult(
        link=Mock(spec=EvidenceSkillLink),
        created=created,
        changed=changed,
    )


def lookup_result(value: object) -> Mock:
    result = Mock()
    result.scalar_one_or_none.return_value = value
    return result


def test_empty_input_calls_factory_only_and_returns_immutable_empty_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate_id = uuid4()
    evidence = make_evidence(uuid4(), candidate_id)
    session = Mock()
    factory = Mock(return_value=())
    builder = Mock()
    adapter = Mock()
    monkeypatch.setattr(orchestration_module, "build_github_evidence_commands", factory)
    monkeypatch.setattr(orchestration_module, "build_github_skill_link_values", builder)
    monkeypatch.setattr(orchestration_module, "persist_github_evidence_skill_link", adapter)

    result = persist_resolved_github_skill_candidates(
        session,
        candidate_id=candidate_id,
        evidence_unit=evidence,
        resolved_candidates=(),
    )

    assert result.persistence_results == ()
    assert isinstance(result.persistence_results, tuple)
    factory.assert_called_once_with(
        candidate_id=candidate_id,
        evidence_unit=evidence,
        resolved_candidates=(),
    )
    builder.assert_not_called()
    adapter.assert_not_called()
    session.execute.assert_not_called()
    session.flush.assert_not_called()
    session.commit.assert_not_called()
    session.rollback.assert_not_called()
    with pytest.raises(FrozenInstanceError):
        result.persistence_results = ()  # type: ignore[misc]


def test_one_signal_flows_factory_builder_adapter_without_context_transformation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate_id = uuid4()
    evidence = make_evidence(uuid4(), candidate_id)
    skill = make_skill("React", uuid4())
    resolved = make_resolved(
        skill,
        manifest="package.json",
        dependency="react",
        rule_id="gh_rule.package.react.v1",
    )
    session = Mock()
    original_builder = orchestration_module.build_github_skill_link_values
    builder_contexts: list[object] = []
    adapter_values: list[GitHubEvidenceSkillLinkValues] = []

    def builder(command: object) -> GitHubEvidenceSkillLinkValues:
        values = original_builder(command)  # type: ignore[arg-type]
        builder_contexts.append(values.context)
        return values

    expected = persistence_result(created=True, changed=True)

    def adapter(
        _session: object, values: GitHubEvidenceSkillLinkValues
    ) -> EvidenceSkillLinkPersistenceResult:
        adapter_values.append(values)
        return expected

    monkeypatch.setattr(orchestration_module, "build_github_skill_link_values", builder)
    monkeypatch.setattr(orchestration_module, "persist_github_evidence_skill_link", adapter)

    result = persist_resolved_github_skill_candidates(
        session,
        candidate_id=candidate_id,
        evidence_unit=evidence,
        resolved_candidates=(resolved,),
    )

    assert result.persistence_results == (expected,)
    assert len(builder_contexts) == 1
    assert adapter_values[0].context is builder_contexts[0]
    assert isinstance(adapter_values[0].context, MappingProxyType)
    assert isinstance(adapter_values[0].context["signals"], tuple)
    assert adapter_values[0].candidate_id == candidate_id
    assert adapter_values[0].evidence_unit_id == evidence.id
    assert adapter_values[0].skill_id == skill.id
    assert adapter_values[0].extraction_method == "deterministic"
    assert adapter_values[0].extraction_version == "github-deterministic-v1"
    assert adapter_values[0].extraction_confidence == Decimal("1.00")
    session.execute.assert_not_called()
    session.flush.assert_not_called()
    session.commit.assert_not_called()
    session.rollback.assert_not_called()


def test_signals_for_one_skill_are_aggregated_once_by_factory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate_id = uuid4()
    evidence = make_evidence(uuid4(), candidate_id)
    skill = make_skill("React", uuid4())
    signals = (
        make_resolved(
            skill,
            manifest="z/package.json",
            dependency="react",
            rule_id="gh_rule.package.react.v1",
        ),
        make_resolved(
            skill,
            manifest="a/package.json",
            dependency="preact",
            rule_id="gh_rule.package.preact.v1",
        ),
    )
    adapter = Mock(return_value=persistence_result(created=True, changed=True))
    monkeypatch.setattr(orchestration_module, "persist_github_evidence_skill_link", adapter)

    result = persist_resolved_github_skill_candidates(
        Mock(),
        candidate_id=candidate_id,
        evidence_unit=evidence,
        resolved_candidates=signals,
    )

    assert len(result.persistence_results) == 1
    assert adapter.call_count == 1
    values = adapter.call_args.args[1]
    assert tuple(signal["manifest"] for signal in values.context["signals"]) == (
        "a/package.json",
        "z/package.json",
    )


def test_multiple_skills_preserve_factory_order_in_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate_id = uuid4()
    evidence = make_evidence(uuid4(), candidate_id)
    react = make_skill("React", UUID("00000000-0000-0000-0000-000000000002"))
    angular = make_skill("Angular", UUID("00000000-0000-0000-0000-000000000001"))
    first = persistence_result(created=True, changed=True)
    second = persistence_result(created=False, changed=False)
    adapter = Mock(side_effect=(first, second))
    monkeypatch.setattr(orchestration_module, "persist_github_evidence_skill_link", adapter)

    result = persist_resolved_github_skill_candidates(
        Mock(),
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

    assert result.persistence_results == (first, second)
    assert [call.args[1].skill_id for call in adapter.call_args_list] == [angular.id, react.id]


def test_repeated_orchestration_preserves_persistence_idempotency() -> None:
    candidate_id = uuid4()
    evidence = make_evidence(uuid4(), candidate_id)
    skill = make_skill("React", uuid4())
    resolved_candidates = (
        make_resolved(
            skill,
            manifest="package.json",
            dependency="react",
            rule_id="gh_rule.package.react.v1",
        ),
    )
    session = Mock()
    session.execute.side_effect = [
        lookup_result(evidence),
        lookup_result(skill),
        lookup_result(None),
    ]

    created = persist_resolved_github_skill_candidates(
        session,
        candidate_id=candidate_id,
        evidence_unit=evidence,
        resolved_candidates=resolved_candidates,
    )
    session.execute.side_effect = [
        lookup_result(evidence),
        lookup_result(skill),
        lookup_result(created.persistence_results[0].link),
    ]

    repeated = persist_resolved_github_skill_candidates(
        session,
        candidate_id=candidate_id,
        evidence_unit=evidence,
        resolved_candidates=resolved_candidates,
    )

    assert created.persistence_results[0].created is True
    assert repeated.persistence_results[0].created is False
    assert repeated.persistence_results[0].changed is False
    session.add.assert_called_once_with(created.persistence_results[0].link)
    session.flush.assert_called_once()
    session.commit.assert_not_called()
    session.rollback.assert_not_called()


def test_factory_candidate_mismatch_propagates_without_builder_or_adapter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate_id = uuid4()
    evidence = make_evidence(uuid4(), uuid4())
    builder = Mock()
    adapter = Mock()
    monkeypatch.setattr(orchestration_module, "build_github_skill_link_values", builder)
    monkeypatch.setattr(orchestration_module, "persist_github_evidence_skill_link", adapter)

    with pytest.raises(EvidenceSkillLinkCandidateMismatchError):
        persist_resolved_github_skill_candidates(
            Mock(),
            candidate_id=candidate_id,
            evidence_unit=evidence,
            resolved_candidates=(),
        )

    builder.assert_not_called()
    adapter.assert_not_called()


def test_adapter_error_stops_following_commands_without_transaction_control(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate_id = uuid4()
    evidence = make_evidence(uuid4(), candidate_id)
    first_skill = make_skill("Angular", uuid4())
    second_skill = make_skill("React", uuid4())
    session = Mock()
    error = RuntimeError("adapter failure")
    adapter = Mock(side_effect=error)
    monkeypatch.setattr(orchestration_module, "persist_github_evidence_skill_link", adapter)

    with pytest.raises(RuntimeError, match="adapter failure") as raised:
        persist_resolved_github_skill_candidates(
            session,
            candidate_id=candidate_id,
            evidence_unit=evidence,
            resolved_candidates=(
                make_resolved(
                    first_skill,
                    manifest="package.json",
                    dependency="angular",
                    rule_id="gh_rule.package.angular.v1",
                ),
                make_resolved(
                    second_skill,
                    manifest="package.json",
                    dependency="react",
                    rule_id="gh_rule.package.react.v1",
                ),
            ),
        )

    assert raised.value is error
    adapter.assert_called_once()
    session.execute.assert_not_called()
    session.flush.assert_not_called()
    session.commit.assert_not_called()
    session.rollback.assert_not_called()


def test_orchestration_contract_has_no_sql_or_boundary_logic() -> None:
    parameters = signature(persist_resolved_github_skill_candidates).parameters
    assert "evidence_unit" in parameters
    assert "evidence_unit_id" not in parameters
    source = getsource(orchestration_module)
    assert "select" not in source
    assert ".execute(" not in source
    assert ".commit(" not in source
    assert ".rollback(" not in source
    assert ".flush(" not in source
    assert "MappingProxyType" not in source
    assert "deep_thaw" not in source
    assert "grouped" not in source
    assert "dedup" not in source
    assert "candidate_id != evidence_unit.candidate_id" not in source
