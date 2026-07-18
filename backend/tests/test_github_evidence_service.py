from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.exc import IntegrityError

from app.integrations.github import GitHubRepositorySnapshot as ProviderSnapshot
from app.models.candidate_profile import CandidateProfile, OnboardingStatus
from app.models.evidence_unit import EvidenceUnit
from app.models.github_repository import GitHubRepository
from app.models.github_repository_snapshot import GitHubRepositorySnapshot
from app.services.candidate import CandidateProfileNotFoundError
from app.services.github_evidence import (
    GitHubRepositorySnapshotNotFoundError,
    generate_github_repository_evidence,
)
from app.services.github_scan import (
    GitHubRepositorySourceNotFoundError,
    GitHubSnapshotIdentityMismatchError,
)
from app.utils.github_evidence import GitHubPersistedSnapshotValidationError
from app.utils.github_snapshot import canonicalize_github_repository_snapshot
from app.utils.github_url import GitHubRepositoryUrlError


def make_candidate(candidate_id: UUID | None = None) -> CandidateProfile:
    return CandidateProfile(
        id=candidate_id or uuid4(),
        user_id=uuid4(),
        display_name="Demo Candidate",
        onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
    )


def make_repository(candidate_id: UUID) -> GitHubRepository:
    return GitHubRepository(
        id=uuid4(),
        candidate_id=candidate_id,
        repository_url="https://github.com/demo-user/demo-api",
    )


def make_provider_snapshot() -> ProviderSnapshot:
    return ProviderSnapshot(
        canonical_url="https://github.com/demo-user/demo-api",
        repository_name="demo-api",
        owner="demo-user",
        description=" Demo repository ",
        default_branch="main",
        is_public=True,
        is_archived=False,
        languages=("Python",),
        file_tree=("README.md", "pyproject.toml"),
        readme_text="Readme",
        manifest_paths=("pyproject.toml",),
        is_demo=True,
    )


def make_snapshot(repository: GitHubRepository) -> GitHubRepositorySnapshot:
    payload = json.loads(
        canonicalize_github_repository_snapshot(make_provider_snapshot()).canonical_json
    )
    snapshot = GitHubRepositorySnapshot(
        id=uuid4(), repository_id=repository.id, checksum="a" * 64, payload=payload
    )
    snapshot.updated_at = datetime(2026, 7, 18, tzinfo=UTC)
    return snapshot


def make_session(
    candidate: CandidateProfile | None,
    repository: GitHubRepository | None,
    snapshot: GitHubRepositorySnapshot | None,
    evidence: EvidenceUnit | None,
) -> Mock:
    session = Mock()
    results = []
    for value in (candidate, repository, snapshot, evidence):
        result = Mock()
        result.scalar_one_or_none.return_value = value
        results.append(result)
    session.execute.side_effect = results
    return session


def test_evidence_model_constraints_and_migration() -> None:
    table = EvidenceUnit.__table__

    assert any(
        isinstance(constraint, CheckConstraint)
        and constraint.name == "ck_evidence_units_ownership_status"
        for constraint in table.constraints
    )
    assert any(
        isinstance(constraint, UniqueConstraint)
        and tuple(column.name for column in constraint.columns)
        == ("candidate_id", "source_type", "source_reference")
        for constraint in table.constraints
    )
    source = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "20260718_0010_github_evidence_constraints.py"
    ).read_text(encoding="utf-8")
    assert 'down_revision: Union[str, None] = "20260718_0009"' in source
    assert "op.create_unique_constraint" in source
    assert "op.drop_constraint" in source


def test_generation_creates_deterministic_repository_evidence() -> None:
    candidate = make_candidate()
    repository = make_repository(candidate.id)
    snapshot = make_snapshot(repository)
    session = make_session(candidate, repository, snapshot, None)

    result = generate_github_repository_evidence(session, candidate.id)

    evidence = result.evidence_unit
    assert result.created is True
    assert result.changed is True
    assert evidence.source_type == "github_repository"
    assert evidence.source_reference == "https://github.com/demo-user/demo-api"
    assert evidence.title == "GitHub repository: demo-user/demo-api"
    assert evidence.description == "Demo repository"
    assert evidence.observed_at == evidence.freshness_at == snapshot.updated_at
    assert evidence.issued_at is None
    assert evidence.verification_status == "source_reachable"
    assert evidence.ownership_status == "unverified"
    assert str(evidence.strength_score) == "1.00"
    assert evidence.raw_payload_reference == f"github_repository_snapshot:{snapshot.id}"
    assert evidence.quality_flags == {
        "archived": False,
        "missing_description": False,
        "missing_readme": False,
        "missing_languages": False,
        "empty_file_tree": False,
        "missing_manifests": False,
    }
    session.add.assert_called_once_with(evidence)
    session.flush.assert_called_once()
    session.commit.assert_not_called()
    session.rollback.assert_not_called()


def test_generation_uses_fallback_description_and_all_quality_flags() -> None:
    candidate = make_candidate()
    repository = make_repository(candidate.id)
    snapshot = make_snapshot(repository)
    snapshot.payload = json.loads(
        canonicalize_github_repository_snapshot(
            replace(
                make_provider_snapshot(),
                description="  ",
                is_archived=True,
                languages=(),
                file_tree=(),
                readme_text=" ",
                manifest_paths=(),
            )
        ).canonical_json
    )
    session = make_session(candidate, repository, snapshot, None)

    evidence = generate_github_repository_evidence(session, candidate.id).evidence_unit

    assert evidence.description == "Public GitHub repository demo-user/demo-api."
    assert evidence.quality_flags == {
        "archived": True,
        "missing_description": True,
        "missing_readme": True,
        "missing_languages": True,
        "empty_file_tree": True,
        "missing_manifests": True,
    }


def test_generation_is_idempotent_without_flush() -> None:
    candidate = make_candidate()
    repository = make_repository(candidate.id)
    snapshot = make_snapshot(repository)
    existing = EvidenceUnit(
        candidate_id=candidate.id,
        source_type="github_repository",
        source_reference="https://github.com/demo-user/demo-api",
        title="GitHub repository: demo-user/demo-api",
        description="Demo repository",
        observed_at=snapshot.updated_at,
        issued_at=None,
        freshness_at=snapshot.updated_at,
        verification_status="source_reachable",
        ownership_status="unverified",
        strength_score=Decimal("1.00"),
        quality_flags={
            "archived": False,
            "missing_description": False,
            "missing_readme": False,
            "missing_languages": False,
            "empty_file_tree": False,
            "missing_manifests": False,
        },
        raw_payload_reference=f"github_repository_snapshot:{snapshot.id}",
    )
    session = make_session(candidate, repository, snapshot, existing)

    result = generate_github_repository_evidence(session, candidate.id)

    assert result.evidence_unit is existing
    assert result.created is False
    assert result.changed is False
    session.add.assert_not_called()
    session.flush.assert_not_called()
    session.commit.assert_not_called()
    session.rollback.assert_not_called()


def test_changed_snapshot_updates_same_evidence_in_place() -> None:
    candidate = make_candidate()
    repository = make_repository(candidate.id)
    snapshot = make_snapshot(repository)
    existing = EvidenceUnit(candidate_id=candidate.id, source_type="github_repository")
    session = make_session(candidate, repository, snapshot, existing)

    result = generate_github_repository_evidence(session, candidate.id)

    assert result.evidence_unit is existing
    assert result.created is False
    assert result.changed is True
    assert existing.source_reference == "https://github.com/demo-user/demo-api"
    session.add.assert_not_called()
    session.flush.assert_called_once()


@pytest.mark.parametrize(
    ("candidate", "repository", "snapshot", "expected_error"),
    [
        (None, None, None, CandidateProfileNotFoundError),
        (make_candidate(), None, None, GitHubRepositorySourceNotFoundError),
    ],
)
def test_generation_rejects_missing_entities(
    candidate: CandidateProfile | None,
    repository: GitHubRepository | None,
    snapshot: GitHubRepositorySnapshot | None,
    expected_error: type[Exception],
) -> None:
    candidate_id = candidate.id if candidate else uuid4()
    session = make_session(candidate, repository, snapshot, None)

    with pytest.raises(expected_error):
        generate_github_repository_evidence(session, candidate_id)

    session.add.assert_not_called()
    session.flush.assert_not_called()


def test_generation_rejects_missing_snapshot() -> None:
    candidate = make_candidate()
    repository = make_repository(candidate.id)
    session = make_session(candidate, repository, None, None)

    with pytest.raises(GitHubRepositorySnapshotNotFoundError):
        generate_github_repository_evidence(session, candidate.id)

    session.add.assert_not_called()
    session.flush.assert_not_called()


@pytest.mark.parametrize(
    ("repository_url", "payload", "expected_error"),
    [
        ("http://github.com/demo-user/demo-api", None, GitHubRepositoryUrlError),
        (
            "https://github.com/demo-user/demo-api",
            {"unexpected": True},
            GitHubPersistedSnapshotValidationError,
        ),
        (
            "https://github.com/demo-user/demo-api",
            "different_identity",
            GitHubSnapshotIdentityMismatchError,
        ),
    ],
)
def test_generation_rejects_invalid_repository_or_snapshot(
    repository_url: str, payload: dict[str, object] | str | None, expected_error: type[Exception]
) -> None:
    candidate = make_candidate()
    repository = make_repository(candidate.id)
    repository.repository_url = repository_url
    snapshot = make_snapshot(repository)
    if payload == "different_identity":
        snapshot.payload["canonical_url"] = "https://github.com/other/repository"
        snapshot.payload["owner"] = "other"
        snapshot.payload["repository_name"] = "repository"
    elif isinstance(payload, dict):
        snapshot.payload = payload
    session = make_session(candidate, repository, snapshot, None)

    with pytest.raises(expected_error):
        generate_github_repository_evidence(session, candidate.id)

    session.add.assert_not_called()
    session.flush.assert_not_called()
    session.commit.assert_not_called()
    session.rollback.assert_not_called()


def test_generation_propagates_integrity_error_without_rollback() -> None:
    candidate = make_candidate()
    repository = make_repository(candidate.id)
    snapshot = make_snapshot(repository)
    session = make_session(candidate, repository, snapshot, None)
    session.flush.side_effect = IntegrityError("insert", {}, Exception("unique violation"))

    with pytest.raises(IntegrityError):
        generate_github_repository_evidence(session, candidate.id)

    session.add.assert_called_once()
    session.flush.assert_called_once()
    session.commit.assert_not_called()
    session.rollback.assert_not_called()
