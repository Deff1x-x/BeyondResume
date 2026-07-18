from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.candidate_profile import CandidateProfile
from app.models.evidence_unit import EvidenceUnit
from app.models.github_repository import GitHubRepository
from app.models.github_repository_snapshot import GitHubRepositorySnapshot
from app.services.candidate import CandidateProfileNotFoundError
from app.services.github_scan import (
    GitHubRepositorySourceNotFoundError,
    GitHubSnapshotIdentityMismatchError,
)
from app.utils.github_evidence import (
    PersistedGitHubRepositoryPayload,
    validate_persisted_github_repository_payload,
)
from app.utils.github_url import parse_github_repository_url


class GitHubRepositorySnapshotNotFoundError(Exception):
    """Raised when a connected repository has no persisted snapshot."""


@dataclass(frozen=True, slots=True)
class GitHubEvidenceGenerationResult:
    evidence_unit: EvidenceUnit
    created: bool
    changed: bool


def generate_github_repository_evidence(
    session: Session, candidate_id: UUID
) -> GitHubEvidenceGenerationResult:
    candidate = session.execute(
        select(CandidateProfile).where(CandidateProfile.id == candidate_id)
    ).scalar_one_or_none()
    if candidate is None:
        raise CandidateProfileNotFoundError

    repository = session.execute(
        select(GitHubRepository).where(GitHubRepository.candidate_id == candidate_id)
    ).scalar_one_or_none()
    if repository is None:
        raise GitHubRepositorySourceNotFoundError

    snapshot = session.execute(
        select(GitHubRepositorySnapshot).where(
            GitHubRepositorySnapshot.repository_id == repository.id
        )
    ).scalar_one_or_none()
    if snapshot is None:
        raise GitHubRepositorySnapshotNotFoundError

    expected_repository = parse_github_repository_url(repository.repository_url)
    payload = validate_persisted_github_repository_payload(snapshot.payload)
    if (
        payload.canonical_url != expected_repository.canonical_url
        or payload.owner != expected_repository.owner
        or payload.repository_name != expected_repository.repository
    ):
        raise GitHubSnapshotIdentityMismatchError
    managed_fields = _managed_evidence_fields(snapshot, payload)
    evidence_unit = session.execute(
        select(EvidenceUnit).where(
            EvidenceUnit.candidate_id == candidate_id,
            EvidenceUnit.source_type == managed_fields["source_type"],
            EvidenceUnit.source_reference == managed_fields["source_reference"],
        )
    ).scalar_one_or_none()

    if evidence_unit is None:
        evidence_unit = EvidenceUnit(candidate_id=candidate_id, **managed_fields)
        session.add(evidence_unit)
        session.flush()
        return GitHubEvidenceGenerationResult(
            evidence_unit=evidence_unit, created=True, changed=True
        )

    if all(getattr(evidence_unit, field) == value for field, value in managed_fields.items()):
        return GitHubEvidenceGenerationResult(
            evidence_unit=evidence_unit, created=False, changed=False
        )

    for field, value in managed_fields.items():
        setattr(evidence_unit, field, value)
    session.flush()
    return GitHubEvidenceGenerationResult(evidence_unit=evidence_unit, created=False, changed=True)


def _managed_evidence_fields(
    snapshot: GitHubRepositorySnapshot, payload: PersistedGitHubRepositoryPayload
) -> dict[str, object]:
    description = payload.description.strip() if payload.description else ""
    if not description:
        description = f"Public GitHub repository {payload.owner}/{payload.repository_name}."
    return {
        "source_type": "github_repository",
        "source_reference": payload.canonical_url,
        "title": f"GitHub repository: {payload.owner}/{payload.repository_name}",
        "description": description,
        "observed_at": snapshot.updated_at,
        "issued_at": None,
        "freshness_at": snapshot.updated_at,
        "verification_status": "source_reachable",
        "ownership_status": "unverified",
        "strength_score": Decimal("1.00"),
        "quality_flags": {
            "archived": payload.is_archived is True,
            "missing_description": not bool(payload.description and payload.description.strip()),
            "missing_readme": not bool(payload.readme_text and payload.readme_text.strip()),
            "missing_languages": not payload.languages,
            "empty_file_tree": not payload.tree_paths,
            "missing_manifests": not payload.manifest_paths,
        },
        "raw_payload_reference": f"github_repository_snapshot:{snapshot.id}",
    }
