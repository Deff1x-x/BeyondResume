from dataclasses import FrozenInstanceError, fields
from uuid import uuid4

import pytest

from app.models.evidence_skill_link import EvidenceSkillLink
from app.models.evidence_unit import EvidenceUnit
from app.models.skill import Skill
from app.services.github_skill_extraction_results import (
    GitHubEvidenceSkillLinkReconciliationResult,
    GitHubSkillCandidateExtractionResult,
    GitHubSkillCandidateResolutionResult,
    GitHubSkillExtractionResult,
    GitHubUnmatchedManifestSignal,
)
from app.services.github_skill_resolution import ResolvedGitHubSkillCandidate
from app.utils.github_skill_extractor import GitHubSkillCandidate
import app.services.github_skill_extraction_results as results_module


def candidate(name: str, rule_id: str) -> GitHubSkillCandidate:
    return GitHubSkillCandidate(
        target_skill_name=name,
        source_dependency=name.lower(),
        source_manifest="package.json",
        manifest_kind="package_json",
        ecosystem="npm",
        signal_type="dependency_manifest",
        rule_id=rule_id,
    )


def evidence() -> EvidenceUnit:
    return EvidenceUnit(id=uuid4(), candidate_id=uuid4(), source_type="github_repository")


def link(source_evidence: EvidenceUnit) -> EvidenceSkillLink:
    return EvidenceSkillLink(
        candidate_id=source_evidence.candidate_id,
        evidence_unit_id=source_evidence.id,
        skill_id=uuid4(),
        extraction_method="deterministic",
        extraction_version="github-deterministic-v1",
        extraction_confidence=1,
        context={},
    )


def resolved(source_candidate: GitHubSkillCandidate) -> ResolvedGitHubSkillCandidate:
    skill = Skill(
        id=uuid4(),
        canonical_name=source_candidate.target_skill_name,
        normalized_name=source_candidate.target_skill_name.lower(),
        category="framework",
        ontology_version="v1",
    )
    return ResolvedGitHubSkillCandidate(
        skill=skill,
        candidate=source_candidate,
        rule_id=source_candidate.rule_id,
    )


def test_exact_v44_field_schemas_and_tuple_order_are_preserved() -> None:
    first = candidate("React", "gh_rule.package.react.v1")
    second = candidate("Vue", "gh_rule.package.vue.v1")
    unmatched = GitHubUnmatchedManifestSignal(
        signal_type="dependency_manifest",
        source_manifest="requirements.txt",
        manifest_kind="requirements_txt",
        ecosystem="python",
        source_dependency="unknown-package",
    )
    extraction = GitHubSkillCandidateExtractionResult((second, first), (unmatched,))
    resolution = GitHubSkillCandidateResolutionResult((resolved(first),), (second,))
    source_evidence = evidence()
    source_link = link(source_evidence)
    reconciliation = GitHubEvidenceSkillLinkReconciliationResult((source_link,), 1, 0, 0, 5)
    final = GitHubSkillExtractionResult(
        source_evidence,
        "github-deterministic-v1",
        (source_link,),
        1,
        0,
        0,
        5,
        (unmatched,),
        (second,),
    )

    assert [field.name for field in fields(GitHubUnmatchedManifestSignal)] == [
        "signal_type",
        "source_manifest",
        "manifest_kind",
        "ecosystem",
        "source_dependency",
    ]
    assert [field.name for field in fields(GitHubSkillCandidateExtractionResult)] == [
        "candidates",
        "unmatched_signals",
    ]
    assert [field.name for field in fields(GitHubSkillCandidateResolutionResult)] == [
        "resolved_candidates",
        "unresolved_rule_targets",
    ]
    assert [field.name for field in fields(GitHubEvidenceSkillLinkReconciliationResult)] == [
        "links",
        "created_count",
        "changed_count",
        "unchanged_count",
        "removed_count",
    ]
    assert [field.name for field in fields(GitHubSkillExtractionResult)] == [
        "evidence_unit",
        "extraction_version",
        "links",
        "created_count",
        "changed_count",
        "unchanged_count",
        "removed_count",
        "unmatched_signals",
        "unresolved_rule_targets",
    ]
    assert extraction.candidates == (second, first)
    assert extraction.unmatched_signals == (unmatched,)
    assert resolution.unresolved_rule_targets == (second,)
    assert reconciliation.links == (source_link,)
    assert final.unmatched_signals == (unmatched,)
    assert final.unresolved_rule_targets == (second,)
    assert not hasattr(extraction, "extracted_candidates")
    assert not hasattr(final, "unmatched_manifest_signals")
    assert not hasattr(final, "unresolved_skill_candidates")


def test_contracts_are_frozen_slots_based_and_require_tuple_collections() -> None:
    source_candidate = candidate("React", "gh_rule.package.react.v1")
    unmatched = GitHubUnmatchedManifestSignal(
        "dependency_manifest", "package.json", "package_json", "npm", "unknown"
    )
    extraction = GitHubSkillCandidateExtractionResult((source_candidate,), (unmatched,))

    with pytest.raises(FrozenInstanceError):
        extraction.candidates = ()  # type: ignore[misc]
    assert hasattr(GitHubSkillCandidateExtractionResult, "__slots__")
    assert isinstance(extraction.candidates, tuple)
    assert isinstance(extraction.unmatched_signals, tuple)
    with pytest.raises(ValueError, match="collections must be tuples"):
        GitHubSkillCandidateExtractionResult((source_candidate,), [unmatched])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="collections must be tuples"):
        GitHubSkillCandidateResolutionResult([], ())  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("counts", "message"),
    [
        ((-1, 0, 0, 0), "non-negative integers"),
        ((0, 0, 0, -1), "non-negative integers"),
        ((0, 0, 0, 1), "account for every link"),
    ],
)
def test_reconciliation_representation_validation(
    counts: tuple[int, int, int, int], message: str
) -> None:
    source_evidence = evidence()
    source_link = link(source_evidence)

    with pytest.raises(ValueError, match=message):
        GitHubEvidenceSkillLinkReconciliationResult((source_link,), *counts)

    valid = GitHubEvidenceSkillLinkReconciliationResult((source_link,), 0, 0, 1, 99)
    assert valid.removed_count == 99


def test_final_result_representation_validation_and_empty_collections() -> None:
    source_evidence = evidence()
    empty = GitHubSkillExtractionResult(
        source_evidence,
        "github-deterministic-v1",
        (),
        0,
        0,
        0,
        0,
        (),
        (),
    )
    assert empty.links == ()
    assert empty.unmatched_signals == ()
    assert empty.unresolved_rule_targets == ()

    with pytest.raises(ValueError, match="account for every link"):
        GitHubSkillExtractionResult(
            source_evidence,
            "github-deterministic-v1",
            (),
            1,
            0,
            0,
            0,
            (),
            (),
        )
    with pytest.raises(ValueError, match="collections must be tuples"):
        GitHubSkillExtractionResult(
            source_evidence,
            "github-deterministic-v1",
            (),
            0,
            0,
            0,
            0,
            [],  # type: ignore[arg-type]
            (),
        )


def test_result_module_has_no_sql_session_mutation_or_service_logic() -> None:
    source = results_module.__file__
    assert source is not None
    content = open(source, encoding="utf-8").read()
    assert "Session" not in content
    assert "select" not in content
    assert ".execute(" not in content
    assert ".flush(" not in content
    assert ".commit(" not in content
    assert ".rollback(" not in content
    assert "session.delete" not in content
    assert "reconcile_" not in content
    assert "Any" not in content
