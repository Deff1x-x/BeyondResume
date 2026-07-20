from dataclasses import replace
from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.exc import IntegrityError

from app.integrations.github import (
    MAX_FILE_TREE_PATHS,
    MAX_LANGUAGES,
    MAX_README_CHARS,
    GitHubRepositorySnapshot as ProviderGitHubRepositorySnapshot,
)
from app.models.github_repository import GitHubRepository
from app.models.github_repository_snapshot import GitHubRepositorySnapshot
from app.services.github_scan import GitHubSnapshotIdentityMismatchError
from app.services.github_snapshot import persist_github_repository_snapshot
from app.utils.github_snapshot import (
    GitHubSnapshotValidationError,
    canonicalize_github_repository_snapshot,
)
from app.utils.github_url import GitHubRepositoryUrlError


def make_provider_snapshot() -> ProviderGitHubRepositorySnapshot:
    return ProviderGitHubRepositorySnapshot(
        canonical_url="https://github.com/demo-user/demo-api",
        repository_name="demo-api",
        owner="demo-user",
        description="Описание",
        default_branch=None,
        is_public=True,
        is_archived=None,
        languages=("Python",),
        file_tree=("README.md", "pyproject.toml"),
        readme_text=None,
        manifest_paths=("pyproject.toml",),
        is_demo=True,
    )


def make_repository() -> GitHubRepository:
    return GitHubRepository(
        id=uuid4(),
        candidate_id=uuid4(),
        repository_url="https://github.com/demo-user/demo-api",
    )


def make_session(existing: GitHubRepositorySnapshot | None) -> Mock:
    session = Mock()
    result = Mock()
    result.scalar_one_or_none.return_value = existing
    session.execute.return_value = result
    return session


def test_snapshot_model_constraints_and_relationship() -> None:
    table = GitHubRepositorySnapshot.__table__

    assert {foreign_key.target_fullname for foreign_key in table.c.repository_id.foreign_keys} == {
        "github_repositories.id"
    }
    assert any(
        isinstance(constraint, UniqueConstraint)
        and tuple(column.name for column in constraint.columns) == ("repository_id",)
        for constraint in table.constraints
    )
    assert any(
        isinstance(constraint, CheckConstraint)
        and constraint.name == "ck_github_repository_snapshots_checksum"
        for constraint in table.constraints
    )
    assert GitHubRepository.snapshot.property.uselist is False


def test_snapshot_migration_has_correct_revision_and_downgrade() -> None:
    migration_path = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "20260718_0009_github_repository_snapshots.py"
    )
    source = migration_path.read_text(encoding="utf-8")

    assert 'down_revision: Union[str, None] = "20260718_0008"' in source
    assert '"github_repository_snapshots"' in source
    assert 'op.drop_table("github_repository_snapshots")' in source


def test_canonicalization_is_stable_and_uses_utf8_json() -> None:
    snapshot = make_provider_snapshot()

    first = canonicalize_github_repository_snapshot(snapshot)
    second = canonicalize_github_repository_snapshot(snapshot)

    assert first == second
    assert first.canonical_json == json.dumps(
        json.loads(first.canonical_json),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    assert "Описание" in first.canonical_json
    assert '"default_branch":null' in first.canonical_json
    assert first.checksum == sha256(first.canonical_json.encode("utf-8")).hexdigest()
    assert set(first.payload) == {
        "canonical_url",
        "default_branch",
        "description",
        "is_archived",
        "is_demo",
        "is_public",
        "languages",
        "manifest_paths",
        "owner",
        "readme_text",
        "repository_name",
        "schema_version",
        "tree_paths",
        "normalized_manifests",
            "manifest_warnings",
            "source_files",
        }
    with pytest.raises(TypeError):
        first.payload["owner"] = "other-owner"  # type: ignore[index]


@pytest.mark.parametrize(
    "snapshot",
    [
        replace(make_provider_snapshot(), languages=("Python",) * (MAX_LANGUAGES + 1)),
        replace(make_provider_snapshot(), file_tree=("path",) * (MAX_FILE_TREE_PATHS + 1)),
        replace(make_provider_snapshot(), manifest_paths=("path",) * (MAX_FILE_TREE_PATHS + 1)),
        replace(make_provider_snapshot(), readme_text="x" * (MAX_README_CHARS + 1)),
    ],
)
def test_canonicalization_rejects_oversized_snapshot(
    snapshot: ProviderGitHubRepositorySnapshot,
) -> None:
    with pytest.raises(GitHubSnapshotValidationError):
        canonicalize_github_repository_snapshot(snapshot)


def test_persistence_creates_snapshot_with_canonical_payload_and_checksum() -> None:
    repository = make_repository()
    session = make_session(None)
    provider_snapshot = make_provider_snapshot()

    result = persist_github_repository_snapshot(session, repository, provider_snapshot)

    assert result.created is True
    assert result.changed is True
    assert result.snapshot.repository_id == repository.id
    assert result.snapshot.payload == json.loads(
        canonicalize_github_repository_snapshot(provider_snapshot).canonical_json
    )
    assert (
        result.snapshot.checksum
        == canonicalize_github_repository_snapshot(provider_snapshot).checksum
    )
    session.add.assert_called_once_with(result.snapshot)
    session.flush.assert_called_once()
    session.commit.assert_not_called()
    session.rollback.assert_not_called()


def test_persistence_is_idempotent_when_checksum_is_unchanged() -> None:
    repository = make_repository()
    canonical = canonicalize_github_repository_snapshot(make_provider_snapshot())
    existing = GitHubRepositorySnapshot(
        repository_id=repository.id,
        checksum=canonical.checksum,
        payload=json.loads(canonical.canonical_json),
    )
    existing.created_at = datetime.now(UTC)
    session = make_session(existing)

    result = persist_github_repository_snapshot(session, repository, make_provider_snapshot())

    assert result.snapshot is existing
    assert result.created is False
    assert result.changed is False
    session.add.assert_not_called()
    session.flush.assert_not_called()
    session.commit.assert_not_called()
    session.rollback.assert_not_called()


def test_persistence_updates_existing_snapshot_when_checksum_changes() -> None:
    repository = make_repository()
    existing = GitHubRepositorySnapshot(
        repository_id=repository.id,
        checksum="a" * 64,
        payload={"canonical_url": "https://github.com/demo-user/demo-api"},
    )
    created_at = datetime.now(UTC)
    existing.created_at = created_at
    session = make_session(existing)
    provider_snapshot = replace(make_provider_snapshot(), description="Updated")

    result = persist_github_repository_snapshot(session, repository, provider_snapshot)

    assert result.snapshot is existing
    assert result.created is False
    assert result.changed is True
    assert existing.created_at == created_at
    assert existing.checksum == canonicalize_github_repository_snapshot(provider_snapshot).checksum
    session.add.assert_not_called()
    session.flush.assert_called_once()
    session.commit.assert_not_called()
    session.rollback.assert_not_called()


@pytest.mark.parametrize(
    "repository_url,snapshot",
    [
        ("http://github.com/demo-user/demo-api", make_provider_snapshot()),
        ("https://github.com/demo-user/demo-api", replace(make_provider_snapshot(), owner="other")),
    ],
)
def test_persistence_rejects_invalid_repository_identity_before_writing(
    repository_url: str, snapshot: ProviderGitHubRepositorySnapshot
) -> None:
    repository = make_repository()
    repository.repository_url = repository_url
    session = make_session(None)

    expected_error = (
        GitHubRepositoryUrlError
        if repository_url.startswith("http://")
        else GitHubSnapshotIdentityMismatchError
    )
    with pytest.raises(expected_error):
        persist_github_repository_snapshot(session, repository, snapshot)

    session.add.assert_not_called()
    session.flush.assert_not_called()
    session.commit.assert_not_called()
    session.rollback.assert_not_called()


def test_persistence_propagates_integrity_error_without_transaction_control() -> None:
    repository = make_repository()
    session = make_session(None)
    session.flush.side_effect = IntegrityError("insert", {}, Exception("constraint violation"))

    with pytest.raises(IntegrityError):
        persist_github_repository_snapshot(session, repository, make_provider_snapshot())

    session.add.assert_called_once()
    session.flush.assert_called_once()
    session.commit.assert_not_called()
    session.rollback.assert_not_called()
