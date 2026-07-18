"""Application use case for persisted GitHub deterministic skill re-extraction."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.candidate_profile import CandidateProfile
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
    _validate_snapshot_identity,
)
from app.services.github_skill_extraction_results import (
    GitHubSkillExtractionResult,
    extract_github_skill_candidate_extraction_result,
    resolve_github_skill_candidate_resolution_result,
)
from app.services.github_skill_link_reconciliation import reconcile_github_evidence_skill_links
from app.services.github_skill_reextraction_errors import GitHubEvidenceSourceConsistencyError
from app.services.github_source_adapter import GitHubSourceAdapter
from app.utils.github_skill_rules import GITHUB_DETERMINISTIC_SKILL_RULES
from app.utils.github_snapshot import read_github_repository_snapshot_payload
from app.utils.github_url import parse_github_repository_url


def reextract_github_evidence_skills(
    session: Session,
    *,
    candidate_id: UUID,
    github_repository_id: UUID,
    evidence_unit_id: UUID,
) -> GitHubSkillExtractionResult:
    """Re-extract deterministic GitHub skills from the current persisted snapshot."""
    candidate = session.execute(
        select(CandidateProfile).where(CandidateProfile.id == candidate_id)
    ).scalar_one_or_none()
    if candidate is None:
        raise CandidateProfileNotFoundError

    repository = session.execute(
        select(GitHubRepository).where(GitHubRepository.id == github_repository_id)
    ).scalar_one_or_none()
    if repository is None:
        raise GitHubRepositorySourceNotFoundError

    persisted_snapshot = session.execute(
        select(GitHubRepositorySnapshot).where(
            GitHubRepositorySnapshot.repository_id == repository.id
        )
    ).scalar_one_or_none()
    if persisted_snapshot is None:
        raise GitHubRepositorySnapshotNotFoundError

    evidence_unit = session.execute(
        select(EvidenceUnit).where(EvidenceUnit.id == evidence_unit_id)
    ).scalar_one_or_none()
    if evidence_unit is None:
        raise EvidenceUnitNotFoundError

    _validate_source_consistency(candidate, repository, persisted_snapshot, evidence_unit)
    snapshot = read_github_repository_snapshot_payload(persisted_snapshot.payload)
    _validate_snapshot_identity(snapshot, parse_github_repository_url(repository.repository_url))

    extraction_result = extract_github_skill_candidate_extraction_result(
        snapshot,
        rules=GITHUB_DETERMINISTIC_SKILL_RULES,
    )
    resolution_result = resolve_github_skill_candidate_resolution_result(
        session,
        extraction_result.candidates,
    )
    reconciliation_result = reconcile_github_evidence_skill_links(
        session,
        candidate_id=candidate_id,
        evidence_unit=evidence_unit,
        resolved_candidates=resolution_result.resolved_candidates,
    )
    return GitHubSkillExtractionResult(
        evidence_unit=evidence_unit,
        extraction_version=GITHUB_DETERMINISTIC_EXTRACTION_VERSION,
        links=reconciliation_result.links,
        created_count=reconciliation_result.created_count,
        changed_count=reconciliation_result.changed_count,
        unchanged_count=reconciliation_result.unchanged_count,
        removed_count=reconciliation_result.removed_count,
        unmatched_signals=extraction_result.unmatched_signals,
        unresolved_rule_targets=resolution_result.unresolved_rule_targets,
    )


def _validate_source_consistency(
    candidate: CandidateProfile,
    repository: GitHubRepository,
    persisted_snapshot: GitHubRepositorySnapshot,
    evidence_unit: EvidenceUnit,
) -> None:
    if repository.candidate_id != candidate.id:
        raise GitHubEvidenceSourceConsistencyError("repository candidate mismatch")
    if evidence_unit.candidate_id != candidate.id:
        raise GitHubEvidenceSourceConsistencyError("evidence unit candidate mismatch")
    if evidence_unit.source_type != GitHubSourceAdapter.source_type:
        raise GitHubEvidenceSourceConsistencyError("evidence unit source type is invalid")
    expected_repository = parse_github_repository_url(repository.repository_url)
    if evidence_unit.source_reference != expected_repository.canonical_url:
        raise GitHubEvidenceSourceConsistencyError("evidence unit source reference mismatch")
    if persisted_snapshot.repository_id != repository.id:
        raise GitHubSnapshotIdentityMismatchError
