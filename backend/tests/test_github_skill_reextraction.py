from inspect import getsource, signature
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.models.candidate_profile import CandidateProfile
from app.models.evidence_skill_link import EvidenceSkillLink
from app.models.evidence_unit import EvidenceUnit
from app.models.github_repository import GitHubRepository
from app.models.github_repository_snapshot import GitHubRepositorySnapshot
from app.services.candidate import CandidateProfileNotFoundError
from app.services.github_evidence import GitHubRepositorySnapshotNotFoundError
from app.services.github_evidence_commands import GITHUB_DETERMINISTIC_EXTRACTION_VERSION
from app.services.github_evidence_persistence_adapter import EvidenceUnitNotFoundError
from app.services.github_scan import (
    GitHubRepositorySourceNotFoundError,
    GitHubSnapshotIdentityMismatchError,
)
from app.services.github_skill_extraction_results import (
    GitHubEvidenceSkillLinkReconciliationResult,
    GitHubSkillCandidateExtractionResult,
    GitHubSkillCandidateResolutionResult,
    GitHubUnmatchedManifestSignal,
)
from app.services.github_skill_reextraction import reextract_github_evidence_skills
from app.services.github_skill_reextraction_errors import GitHubEvidenceSourceConsistencyError
from app.utils.github_skill_extractor import GitHubSkillCandidate
import app.services.github_skill_reextraction as reextraction_module


def lookup_result(value: object) -> Mock:
    result = Mock()
    result.scalar_one_or_none.return_value = value
    return result


def candidate() -> Mock:
    value = Mock(spec=CandidateProfile)
    value.id = uuid4()
    return value


def repository(candidate_id: object) -> Mock:
    value = Mock(spec=GitHubRepository)
    value.id = uuid4()
    value.candidate_id = candidate_id
    value.repository_url = "https://github.com/octo/example"
    return value


def persisted_snapshot(repository_id: object) -> Mock:
    value = Mock(spec=GitHubRepositorySnapshot)
    value.repository_id = repository_id
    value.payload = {"stored": "payload"}
    return value


def evidence_unit(candidate_id: object) -> Mock:
    value = Mock(spec=EvidenceUnit)
    value.id = uuid4()
    value.candidate_id = candidate_id
    value.source_type = "github_repository"
    value.source_reference = "https://github.com/octo/example"
    return value


def extraction_result() -> GitHubSkillCandidateExtractionResult:
    unmatched = GitHubUnmatchedManifestSignal(
        signal_type="dependency_manifest",
        source_manifest="package.json",
        manifest_kind="package_json",
        ecosystem="npm",
        source_dependency="unknown",
    )
    source_candidate = GitHubSkillCandidate(
        target_skill_name="React",
        source_dependency="react",
        source_manifest="package.json",
        manifest_kind="package_json",
        ecosystem="npm",
        signal_type="dependency_manifest",
        rule_id="gh_rule.package.react.v1",
    )
    return GitHubSkillCandidateExtractionResult((source_candidate,), (unmatched,))


def prepare_successful_dependencies(session: Mock) -> tuple[Mock, Mock, Mock, Mock]:
    source_candidate = candidate()
    source_repository = repository(source_candidate.id)
    source_snapshot = persisted_snapshot(source_repository.id)
    source_evidence = evidence_unit(source_candidate.id)
    session.execute.side_effect = [
        lookup_result(source_candidate),
        lookup_result(source_repository),
        lookup_result(source_snapshot),
        lookup_result(source_evidence),
    ]
    return source_candidate, source_repository, source_snapshot, source_evidence


def test_public_contract_and_persisted_pipeline_composition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = Mock()
    source_candidate, source_repository, source_snapshot, source_evidence = (
        prepare_successful_dependencies(session)
    )
    persisted_dto = Mock()
    extraction = extraction_result()
    resolution = GitHubSkillCandidateResolutionResult((), extraction.candidates)
    final_link = Mock(spec=EvidenceSkillLink)
    reconciliation = GitHubEvidenceSkillLinkReconciliationResult((final_link,), 1, 0, 0, 2)
    reader = Mock(return_value=persisted_dto)
    identity_validator = Mock()
    extractor = Mock(return_value=extraction)
    resolver = Mock(return_value=resolution)
    reconcile = Mock(return_value=reconciliation)
    monkeypatch.setattr(reextraction_module, "read_github_repository_snapshot_payload", reader)
    monkeypatch.setattr(reextraction_module, "_validate_snapshot_identity", identity_validator)
    monkeypatch.setattr(
        reextraction_module, "extract_github_skill_candidate_extraction_result", extractor
    )
    monkeypatch.setattr(
        reextraction_module, "resolve_github_skill_candidate_resolution_result", resolver
    )
    monkeypatch.setattr(reextraction_module, "reconcile_github_evidence_skill_links", reconcile)

    result = reextract_github_evidence_skills(
        session,
        candidate_id=source_candidate.id,
        github_repository_id=source_repository.id,
        evidence_unit_id=source_evidence.id,
    )

    assert list(signature(reextract_github_evidence_skills).parameters) == [
        "session",
        "candidate_id",
        "github_repository_id",
        "evidence_unit_id",
    ]
    reader.assert_called_once_with(source_snapshot.payload)
    extractor.assert_called_once_with(
        persisted_dto,
        rules=reextraction_module.GITHUB_DETERMINISTIC_SKILL_RULES,
    )
    resolver.assert_called_once_with(session, extraction.candidates)
    reconcile.assert_called_once_with(
        session,
        candidate_id=source_candidate.id,
        evidence_unit=source_evidence,
        resolved_candidates=resolution.resolved_candidates,
    )
    assert result.evidence_unit is source_evidence
    assert result.extraction_version == GITHUB_DETERMINISTIC_EXTRACTION_VERSION
    assert result.links == reconciliation.links
    assert result.created_count == reconciliation.created_count
    assert result.changed_count == reconciliation.changed_count
    assert result.unchanged_count == reconciliation.unchanged_count
    assert result.removed_count == reconciliation.removed_count
    assert result.unmatched_signals == extraction.unmatched_signals
    assert result.unresolved_rule_targets == resolution.unresolved_rule_targets
    session.commit.assert_not_called()
    session.rollback.assert_not_called()
    session.begin.assert_not_called()
    session.begin_nested.assert_not_called()


@pytest.mark.parametrize(
    ("missing_index", "error_type"),
    [
        (0, CandidateProfileNotFoundError),
        (1, GitHubRepositorySourceNotFoundError),
        (2, GitHubRepositorySnapshotNotFoundError),
        (3, EvidenceUnitNotFoundError),
    ],
)
def test_required_lookups_raise_existing_typed_errors(
    missing_index: int,
    error_type: type[Exception],
) -> None:
    session = Mock()
    source_candidate = candidate()
    source_repository = repository(source_candidate.id)
    source_snapshot = persisted_snapshot(source_repository.id)
    source_evidence = evidence_unit(source_candidate.id)
    values: list[object | None] = [
        source_candidate,
        source_repository,
        source_snapshot,
        source_evidence,
    ]
    values[missing_index] = None
    session.execute.side_effect = [lookup_result(value) for value in values[: missing_index + 1]]

    with pytest.raises(error_type):
        reextract_github_evidence_skills(
            session,
            candidate_id=source_candidate.id,
            github_repository_id=source_repository.id,
            evidence_unit_id=source_evidence.id,
        )


@pytest.mark.parametrize(
    "mutate",
    [
        lambda source_candidate, source_repository, source_snapshot, source_evidence: setattr(
            source_repository, "candidate_id", uuid4()
        ),
        lambda source_candidate, source_repository, source_snapshot, source_evidence: setattr(
            source_evidence, "candidate_id", uuid4()
        ),
        lambda source_candidate, source_repository, source_snapshot, source_evidence: setattr(
            source_evidence, "source_type", "manual"
        ),
        lambda source_candidate, source_repository, source_snapshot, source_evidence: setattr(
            source_evidence, "source_reference", "https://github.com/other/repository"
        ),
    ],
)
def test_source_consistency_fails_before_reader_or_pipeline(
    monkeypatch: pytest.MonkeyPatch,
    mutate: object,
) -> None:
    session = Mock()
    source_candidate, source_repository, source_snapshot, source_evidence = (
        prepare_successful_dependencies(session)
    )
    mutate(source_candidate, source_repository, source_snapshot, source_evidence)  # type: ignore[operator]
    reader = Mock()
    extractor = Mock()
    resolver = Mock()
    reconcile = Mock()
    monkeypatch.setattr(reextraction_module, "read_github_repository_snapshot_payload", reader)
    monkeypatch.setattr(
        reextraction_module, "extract_github_skill_candidate_extraction_result", extractor
    )
    monkeypatch.setattr(
        reextraction_module, "resolve_github_skill_candidate_resolution_result", resolver
    )
    monkeypatch.setattr(reextraction_module, "reconcile_github_evidence_skill_links", reconcile)

    with pytest.raises(GitHubEvidenceSourceConsistencyError):
        reextract_github_evidence_skills(
            session,
            candidate_id=source_candidate.id,
            github_repository_id=source_repository.id,
            evidence_unit_id=source_evidence.id,
        )

    reader.assert_not_called()
    extractor.assert_not_called()
    resolver.assert_not_called()
    reconcile.assert_not_called()


def test_snapshot_identity_error_is_not_transformed(monkeypatch: pytest.MonkeyPatch) -> None:
    session = Mock()
    source_candidate, source_repository, source_snapshot, source_evidence = (
        prepare_successful_dependencies(session)
    )
    reader = Mock(return_value=Mock())
    error = GitHubSnapshotIdentityMismatchError()
    monkeypatch.setattr(reextraction_module, "read_github_repository_snapshot_payload", reader)
    monkeypatch.setattr(reextraction_module, "_validate_snapshot_identity", Mock(side_effect=error))

    with pytest.raises(GitHubSnapshotIdentityMismatchError) as raised:
        reextract_github_evidence_skills(
            session,
            candidate_id=source_candidate.id,
            github_repository_id=source_repository.id,
            evidence_unit_id=source_evidence.id,
        )

    assert raised.value is error
    reader.assert_called_once_with(source_snapshot.payload)


@pytest.mark.parametrize(
    "boundary_name",
    [
        "extract_github_skill_candidate_extraction_result",
        "resolve_github_skill_candidate_resolution_result",
        "reconcile_github_evidence_skill_links",
    ],
)
def test_pipeline_errors_propagate_unchanged(
    monkeypatch: pytest.MonkeyPatch,
    boundary_name: str,
) -> None:
    session = Mock()
    source_candidate, source_repository, _, source_evidence = prepare_successful_dependencies(
        session
    )
    extraction = extraction_result()
    monkeypatch.setattr(
        reextraction_module, "read_github_repository_snapshot_payload", Mock(return_value=Mock())
    )
    monkeypatch.setattr(reextraction_module, "_validate_snapshot_identity", Mock())
    monkeypatch.setattr(
        reextraction_module,
        "extract_github_skill_candidate_extraction_result",
        Mock(return_value=extraction),
    )
    monkeypatch.setattr(
        reextraction_module,
        "resolve_github_skill_candidate_resolution_result",
        Mock(return_value=GitHubSkillCandidateResolutionResult((), ())),
    )
    error = RuntimeError(boundary_name)
    monkeypatch.setattr(reextraction_module, boundary_name, Mock(side_effect=error))

    with pytest.raises(RuntimeError, match=boundary_name) as raised:
        reextract_github_evidence_skills(
            session,
            candidate_id=source_candidate.id,
            github_repository_id=source_repository.id,
            evidence_unit_id=source_evidence.id,
        )

    assert raised.value is error


def test_empty_candidates_reach_resolution_and_authoritative_reconciliation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = Mock()
    source_candidate, source_repository, _, source_evidence = prepare_successful_dependencies(
        session
    )
    extraction = GitHubSkillCandidateExtractionResult((), ())
    resolution = GitHubSkillCandidateResolutionResult((), ())
    monkeypatch.setattr(
        reextraction_module, "read_github_repository_snapshot_payload", Mock(return_value=Mock())
    )
    monkeypatch.setattr(reextraction_module, "_validate_snapshot_identity", Mock())
    monkeypatch.setattr(
        reextraction_module,
        "extract_github_skill_candidate_extraction_result",
        Mock(return_value=extraction),
    )
    resolver = Mock(return_value=resolution)
    reconcile = Mock(return_value=GitHubEvidenceSkillLinkReconciliationResult((), 0, 0, 0, 3))
    monkeypatch.setattr(
        reextraction_module, "resolve_github_skill_candidate_resolution_result", resolver
    )
    monkeypatch.setattr(reextraction_module, "reconcile_github_evidence_skill_links", reconcile)

    result = reextract_github_evidence_skills(
        session,
        candidate_id=source_candidate.id,
        github_repository_id=source_repository.id,
        evidence_unit_id=source_evidence.id,
    )

    resolver.assert_called_once_with(session, ())
    reconcile.assert_called_once_with(
        session,
        candidate_id=source_candidate.id,
        evidence_unit=source_evidence,
        resolved_candidates=(),
    )
    assert result.removed_count == 3


def test_application_service_has_no_provider_scan_or_direct_lower_boundaries() -> None:
    source = getsource(reextraction_module)

    assert "run_github_repository_scan" not in source
    assert "extract_github_skill_candidates(" not in source
    assert "resolve_github_skill_candidates(" not in source
    assert "build_github_evidence_commands" not in source
    assert "build_github_skill_link_values" not in source
    assert "persist_github_evidence_skill_link" not in source
    assert "persist_resolved_github_skill_candidates" not in source
    assert ".delete(" not in source
    assert ".commit(" not in source
    assert ".rollback(" not in source
    assert ".begin(" not in source
    assert ".begin_nested(" not in source
