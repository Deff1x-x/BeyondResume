from decimal import Decimal
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
    InvalidExtractionContextError,
)
from app.services.github_evidence_persistence_adapter import (
    EvidenceUnitNotFoundError,
    persist_github_evidence_skill_link,
)
from app.services.github_evidence_skill_link_builder import GitHubEvidenceSkillLinkValues
from app.services.skill_ontology import SkillNotFoundError
import app.services.github_evidence_persistence_adapter as adapter_module


def make_evidence(evidence_unit_id: UUID, candidate_id: UUID) -> EvidenceUnit:
    return EvidenceUnit(
        id=evidence_unit_id,
        candidate_id=candidate_id,
        source_type="github_repository",
    )


def make_skill(skill_id: UUID) -> Skill:
    return Skill(
        id=skill_id,
        canonical_name="React",
        normalized_name="react",
        category="framework",
        ontology_version="v1",
    )


def make_values(
    *,
    candidate_id: UUID | None = None,
    evidence_unit_id: UUID | None = None,
    skill_id: UUID | None = None,
    context: MappingProxyType | None = None,
) -> GitHubEvidenceSkillLinkValues:
    return GitHubEvidenceSkillLinkValues(
        candidate_id=candidate_id or uuid4(),
        evidence_unit_id=evidence_unit_id or uuid4(),
        skill_id=skill_id or uuid4(),
        extraction_method="deterministic",
        extraction_version="github-deterministic-v1",
        extraction_confidence=Decimal("1.00"),
        context=context
        or MappingProxyType(
            {
                "extractor": "github_deterministic",
                "version": "github-deterministic-v1",
                "signals": (
                    MappingProxyType(
                        {
                            "type": "dependency_manifest",
                            "manifest": "package.json",
                            "manifest_kind": "package_json",
                            "ecosystem": "npm",
                            "matched_value": "react",
                            "rule_id": "gh_rule.package.react.v1",
                        }
                    ),
                    MappingProxyType(
                        {
                            "type": "dependency_manifest",
                            "manifest": "requirements.txt",
                            "manifest_kind": "requirements_txt",
                            "ecosystem": "python",
                            "matched_value": "requests",
                            "rule_id": "gh_rule.python.requests.v1",
                        }
                    ),
                ),
            }
        ),
    )


def lookup_result(value: object) -> Mock:
    result = Mock()
    result.scalar_one_or_none.return_value = value
    return result


def test_adapter_loads_entities_thaws_context_and_delegates_without_transaction_control(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    values = make_values()
    evidence_unit = make_evidence(values.evidence_unit_id, values.candidate_id)
    skill = make_skill(values.skill_id)
    session = Mock()
    session.execute.side_effect = [lookup_result(evidence_unit), lookup_result(skill)]
    expected = EvidenceSkillLinkPersistenceResult(
        link=Mock(spec=EvidenceSkillLink), created=True, changed=True
    )
    persist = Mock(return_value=expected)
    monkeypatch.setattr(adapter_module, "persist_evidence_skill_link", persist)

    assert persist_github_evidence_skill_link(session, values) is expected

    assert session.execute.call_count == 2
    persist.assert_called_once()
    _, keyword_args = persist.call_args
    assert keyword_args["candidate_id"] == values.candidate_id
    assert keyword_args["evidence_unit"] is evidence_unit
    assert keyword_args["skill"] is skill
    assert keyword_args["extraction_method"] == values.extraction_method
    assert keyword_args["extraction_version"] == values.extraction_version
    assert keyword_args["extraction_confidence"] == values.extraction_confidence
    context = keyword_args["context"]
    assert context is not values.context
    assert isinstance(context, dict)
    assert isinstance(context["signals"], list)
    assert isinstance(context["signals"][0], dict)
    assert context == {
        "extractor": "github_deterministic",
        "version": "github-deterministic-v1",
        "signals": [
            {
                "type": "dependency_manifest",
                "manifest": "package.json",
                "manifest_kind": "package_json",
                "ecosystem": "npm",
                "matched_value": "react",
                "rule_id": "gh_rule.package.react.v1",
            },
            {
                "type": "dependency_manifest",
                "manifest": "requirements.txt",
                "manifest_kind": "requirements_txt",
                "ecosystem": "python",
                "matched_value": "requests",
                "rule_id": "gh_rule.python.requests.v1",
            },
        ],
    }
    assert [signal["manifest"] for signal in context["signals"]] == [
        "package.json",
        "requirements.txt",
    ]
    assert isinstance(values.context, MappingProxyType)
    assert isinstance(values.context["signals"], tuple)
    assert isinstance(values.context["signals"][0], MappingProxyType)
    session.commit.assert_not_called()
    session.rollback.assert_not_called()
    session.flush.assert_not_called()


def test_adapter_rejects_missing_evidence_unit_without_loading_skill() -> None:
    session = Mock()
    session.execute.return_value = lookup_result(None)

    with pytest.raises(EvidenceUnitNotFoundError):
        persist_github_evidence_skill_link(session, make_values())

    assert session.execute.call_count == 1
    session.commit.assert_not_called()
    session.rollback.assert_not_called()
    session.flush.assert_not_called()


def test_adapter_persists_new_link_through_existing_service() -> None:
    values = make_values()
    evidence_unit = make_evidence(values.evidence_unit_id, values.candidate_id)
    skill = make_skill(values.skill_id)
    session = Mock()
    session.execute.side_effect = [
        lookup_result(evidence_unit),
        lookup_result(skill),
        lookup_result(None),
    ]

    result = persist_github_evidence_skill_link(session, values)

    assert result.created is True
    assert result.changed is True
    assert result.link.candidate_id == values.candidate_id
    assert result.link.evidence_unit_id == values.evidence_unit_id
    assert result.link.skill_id == values.skill_id
    assert result.link.extraction_method == values.extraction_method
    assert result.link.extraction_version == values.extraction_version
    assert result.link.extraction_confidence == values.extraction_confidence
    assert result.link.context["signals"] == [
        {
            "type": "dependency_manifest",
            "manifest": "package.json",
            "manifest_kind": "package_json",
            "ecosystem": "npm",
            "matched_value": "react",
            "rule_id": "gh_rule.package.react.v1",
        },
        {
            "type": "dependency_manifest",
            "manifest": "requirements.txt",
            "manifest_kind": "requirements_txt",
            "ecosystem": "python",
            "matched_value": "requests",
            "rule_id": "gh_rule.python.requests.v1",
        },
    ]
    session.add.assert_called_once_with(result.link)
    session.flush.assert_called_once()
    session.commit.assert_not_called()
    session.rollback.assert_not_called()


def test_adapter_rejects_missing_skill() -> None:
    values = make_values()
    session = Mock()
    session.execute.side_effect = [
        lookup_result(make_evidence(values.evidence_unit_id, values.candidate_id)),
        lookup_result(None),
    ]

    with pytest.raises(SkillNotFoundError):
        persist_github_evidence_skill_link(session, values)

    assert session.execute.call_count == 2
    session.commit.assert_not_called()
    session.rollback.assert_not_called()
    session.flush.assert_not_called()


def test_adapter_preserves_existing_candidate_mismatch_error() -> None:
    values = make_values()
    session = Mock()
    session.execute.side_effect = [
        lookup_result(make_evidence(values.evidence_unit_id, uuid4())),
        lookup_result(make_skill(values.skill_id)),
    ]

    with pytest.raises(EvidenceSkillLinkCandidateMismatchError):
        persist_github_evidence_skill_link(session, values)

    session.commit.assert_not_called()
    session.rollback.assert_not_called()
    session.flush.assert_not_called()


def test_adapter_rejects_unsupported_nested_context_value_before_persistence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    values = make_values(
        context=MappingProxyType({"signals": (MappingProxyType({"bad": object()}),)})
    )
    session = Mock()
    session.execute.side_effect = [
        lookup_result(make_evidence(values.evidence_unit_id, values.candidate_id)),
        lookup_result(make_skill(values.skill_id)),
    ]
    persist = Mock()
    monkeypatch.setattr(adapter_module, "persist_evidence_skill_link", persist)

    with pytest.raises(InvalidExtractionContextError):
        persist_github_evidence_skill_link(session, values)

    persist.assert_not_called()
    session.commit.assert_not_called()
    session.rollback.assert_not_called()
    session.flush.assert_not_called()


def test_repeated_adapter_call_preserves_existing_idempotency_semantics() -> None:
    values = make_values()
    evidence_unit = make_evidence(values.evidence_unit_id, values.candidate_id)
    skill = make_skill(values.skill_id)
    session = Mock()
    session.execute.side_effect = [
        lookup_result(evidence_unit),
        lookup_result(skill),
        lookup_result(None),
    ]

    created = persist_github_evidence_skill_link(session, values)
    session.execute.side_effect = [
        lookup_result(evidence_unit),
        lookup_result(skill),
        lookup_result(created.link),
    ]
    repeated = persist_github_evidence_skill_link(session, values)

    assert created.created is True
    assert created.changed is True
    assert repeated == EvidenceSkillLinkPersistenceResult(
        link=created.link, created=False, changed=False
    )
    session.add.assert_called_once_with(created.link)
    session.flush.assert_called_once()
    session.commit.assert_not_called()
    session.rollback.assert_not_called()
