from dataclasses import FrozenInstanceError
from decimal import Decimal
from inspect import getsource
from types import MappingProxyType
from uuid import uuid4

import pytest

from app.services.github_evidence_commands import GitHubEvidenceCommand
from app.services.github_evidence_skill_link_builder import (
    GitHubEvidenceSkillLinkValues,
    build_github_skill_link_values,
)
import app.services.github_evidence_skill_link_builder as builder_module


def make_command() -> GitHubEvidenceCommand:
    signal = MappingProxyType(
        {
            "type": "dependency_manifest",
            "manifest": "package.json",
            "manifest_kind": "package_json",
            "ecosystem": "npm",
            "matched_value": "react",
            "rule_id": "gh_rule.package.react.v1",
        }
    )
    return GitHubEvidenceCommand(
        candidate_id=uuid4(),
        evidence_unit_id=uuid4(),
        skill_id=uuid4(),
        extraction_method="deterministic",
        extraction_version="github-deterministic-v1",
        extraction_confidence=Decimal("1.00"),
        context=MappingProxyType(
            {
                "extractor": "github_deterministic",
                "version": "github-deterministic-v1",
                "signals": (signal,),
            }
        ),
    )


def test_builder_copies_every_command_field_without_transforming_context() -> None:
    command = make_command()

    values = build_github_skill_link_values(command)

    assert values.candidate_id == command.candidate_id
    assert values.evidence_unit_id == command.evidence_unit_id
    assert values.skill_id == command.skill_id
    assert values.extraction_method == command.extraction_method
    assert values.extraction_version == command.extraction_version
    assert values.extraction_confidence == command.extraction_confidence
    assert values.context is command.context
    assert values.context["signals"] is command.context["signals"]
    assert values.context["signals"][0] is command.context["signals"][0]


def test_builder_is_deterministic_and_does_not_mutate_command() -> None:
    command = make_command()

    first = build_github_skill_link_values(command)
    second = build_github_skill_link_values(command)

    assert first == second
    assert command.context["signals"][0]["rule_id"] == "gh_rule.package.react.v1"


def test_values_are_immutable_and_builder_has_no_orm_or_persistence_inputs() -> None:
    values = build_github_skill_link_values(make_command())

    with pytest.raises(FrozenInstanceError):
        values.skill_id = uuid4()  # type: ignore[misc]
    with pytest.raises(TypeError):
        values.context["version"] = "changed"  # type: ignore[index]
    with pytest.raises(TypeError):
        values.context["signals"][0]["rule_id"] = "changed"  # type: ignore[index]

    source = getsource(builder_module)
    assert "sqlalchemy" not in source
    assert "Session" not in source
    assert "persist_evidence_skill_link" not in source
    assert GitHubEvidenceSkillLinkValues.__dataclass_params__.frozen is True
