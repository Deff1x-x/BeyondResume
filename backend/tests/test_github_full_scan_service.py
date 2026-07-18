from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.integrations.github import GitHubProvider, GitHubRepositoryNotFoundError
from app.models.evidence_unit import EvidenceUnit
from app.models.github_repository import GitHubRepository
from app.models.github_repository_snapshot import GitHubRepositorySnapshot
from app.services.github_evidence import GitHubEvidenceGenerationResult
from app.services.github_full_scan import run_github_repository_scan
from app.services.github_scan import GitHubRepositorySourceNotFoundError
from app.services.github_snapshot import GitHubRepositorySnapshotPersistenceResult


def make_session(repository: GitHubRepository | None) -> Mock:
    session = Mock()
    result = Mock()
    result.scalar_one_or_none.return_value = repository
    session.execute.return_value = result
    return session


def test_full_scan_calls_stages_in_order_and_returns_first_scan_flags(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate_id = uuid4()
    repository = GitHubRepository(id=uuid4(), candidate_id=candidate_id, repository_url="url")
    persisted_snapshot = GitHubRepositorySnapshot(id=uuid4(), repository_id=repository.id)
    evidence_unit = EvidenceUnit(candidate_id=candidate_id, source_type="github_repository")
    session = make_session(repository)
    provider = Mock(spec=GitHubProvider)
    calls: list[str] = []

    def fetch(*_args: object) -> object:
        calls.append("fetch")
        return object()

    def persist(*_args: object) -> GitHubRepositorySnapshotPersistenceResult:
        calls.append("persist")
        return GitHubRepositorySnapshotPersistenceResult(persisted_snapshot, True, True)

    def generate(*_args: object) -> GitHubEvidenceGenerationResult:
        calls.append("evidence")
        return GitHubEvidenceGenerationResult(evidence_unit, True, True)

    monkeypatch.setattr("app.services.github_full_scan.fetch_github_repository_snapshot", fetch)
    monkeypatch.setattr("app.services.github_full_scan.persist_github_repository_snapshot", persist)
    monkeypatch.setattr(
        "app.services.github_full_scan.generate_github_repository_evidence", generate
    )

    result = run_github_repository_scan(session, candidate_id, provider)

    assert calls == ["fetch", "persist", "evidence"]
    assert result.repository is repository
    assert result.persisted_snapshot is persisted_snapshot
    assert result.evidence_unit is evidence_unit
    assert (
        result.snapshot_created,
        result.snapshot_changed,
        result.evidence_created,
        result.evidence_changed,
    ) == (True, True, True, True)
    session.commit.assert_not_called()
    session.rollback.assert_not_called()


def test_full_scan_returns_all_false_for_unchanged_scan(monkeypatch: pytest.MonkeyPatch) -> None:
    candidate_id = uuid4()
    repository = GitHubRepository(id=uuid4(), candidate_id=candidate_id, repository_url="url")
    persisted_snapshot = GitHubRepositorySnapshot(id=uuid4(), repository_id=repository.id)
    evidence_unit = EvidenceUnit(candidate_id=candidate_id, source_type="github_repository")
    session = make_session(repository)

    monkeypatch.setattr(
        "app.services.github_full_scan.fetch_github_repository_snapshot", lambda *_args: object()
    )
    monkeypatch.setattr(
        "app.services.github_full_scan.persist_github_repository_snapshot",
        lambda *_args: GitHubRepositorySnapshotPersistenceResult(persisted_snapshot, False, False),
    )
    monkeypatch.setattr(
        "app.services.github_full_scan.generate_github_repository_evidence",
        lambda *_args: GitHubEvidenceGenerationResult(evidence_unit, False, False),
    )

    result = run_github_repository_scan(session, candidate_id, Mock(spec=GitHubProvider))

    assert (
        result.snapshot_created,
        result.snapshot_changed,
        result.evidence_created,
        result.evidence_changed,
    ) == (False, False, False, False)
    session.flush.assert_not_called()


def test_full_scan_returns_update_flags_without_creating_new_entities(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate_id = uuid4()
    repository = GitHubRepository(id=uuid4(), candidate_id=candidate_id, repository_url="url")
    persisted_snapshot = GitHubRepositorySnapshot(id=uuid4(), repository_id=repository.id)
    evidence_unit = EvidenceUnit(candidate_id=candidate_id, source_type="github_repository")
    session = make_session(repository)
    monkeypatch.setattr(
        "app.services.github_full_scan.fetch_github_repository_snapshot", lambda *_args: object()
    )
    monkeypatch.setattr(
        "app.services.github_full_scan.persist_github_repository_snapshot",
        lambda *_args: GitHubRepositorySnapshotPersistenceResult(persisted_snapshot, False, True),
    )
    monkeypatch.setattr(
        "app.services.github_full_scan.generate_github_repository_evidence",
        lambda *_args: GitHubEvidenceGenerationResult(evidence_unit, False, True),
    )

    result = run_github_repository_scan(session, candidate_id, Mock(spec=GitHubProvider))

    assert result.persisted_snapshot is persisted_snapshot
    assert result.evidence_unit is evidence_unit
    assert (result.snapshot_created, result.snapshot_changed) == (False, True)
    assert (result.evidence_created, result.evidence_changed) == (False, True)


def test_fetch_error_short_circuits_remaining_stages(monkeypatch: pytest.MonkeyPatch) -> None:
    session = make_session(None)
    error = GitHubRepositoryNotFoundError()
    persist = Mock()
    generate = Mock()
    monkeypatch.setattr(
        "app.services.github_full_scan.fetch_github_repository_snapshot",
        Mock(side_effect=error),
    )
    monkeypatch.setattr("app.services.github_full_scan.persist_github_repository_snapshot", persist)
    monkeypatch.setattr(
        "app.services.github_full_scan.generate_github_repository_evidence", generate
    )

    with pytest.raises(GitHubRepositoryNotFoundError):
        run_github_repository_scan(session, uuid4(), Mock(spec=GitHubProvider))

    persist.assert_not_called()
    generate.assert_not_called()


def test_persistence_error_short_circuits_evidence_and_integrity_error_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate_id = uuid4()
    repository = GitHubRepository(id=uuid4(), candidate_id=candidate_id, repository_url="url")
    session = make_session(repository)
    generate = Mock()
    error = IntegrityError("insert", {}, Exception("constraint violation"))
    monkeypatch.setattr(
        "app.services.github_full_scan.fetch_github_repository_snapshot", lambda *_args: object()
    )
    monkeypatch.setattr(
        "app.services.github_full_scan.persist_github_repository_snapshot", Mock(side_effect=error)
    )
    monkeypatch.setattr(
        "app.services.github_full_scan.generate_github_repository_evidence", generate
    )

    with pytest.raises(IntegrityError):
        run_github_repository_scan(session, candidate_id, Mock(spec=GitHubProvider))

    generate.assert_not_called()
    session.commit.assert_not_called()
    session.rollback.assert_not_called()


def test_evidence_error_propagates_without_transaction_control(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate_id = uuid4()
    repository = GitHubRepository(id=uuid4(), candidate_id=candidate_id, repository_url="url")
    session = make_session(repository)
    error = RuntimeError("generation failed")
    monkeypatch.setattr(
        "app.services.github_full_scan.fetch_github_repository_snapshot", lambda *_args: object()
    )
    monkeypatch.setattr(
        "app.services.github_full_scan.persist_github_repository_snapshot",
        lambda *_args: GitHubRepositorySnapshotPersistenceResult(
            GitHubRepositorySnapshot(id=uuid4(), repository_id=repository.id), False, False
        ),
    )
    monkeypatch.setattr(
        "app.services.github_full_scan.generate_github_repository_evidence", Mock(side_effect=error)
    )

    with pytest.raises(RuntimeError, match="generation failed"):
        run_github_repository_scan(session, candidate_id, Mock(spec=GitHubProvider))

    session.commit.assert_not_called()
    session.rollback.assert_not_called()


def test_repository_disappearing_after_fetch_is_controlled_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = make_session(None)
    persist = Mock()
    generate = Mock()
    monkeypatch.setattr(
        "app.services.github_full_scan.fetch_github_repository_snapshot", lambda *_args: object()
    )
    monkeypatch.setattr("app.services.github_full_scan.persist_github_repository_snapshot", persist)
    monkeypatch.setattr(
        "app.services.github_full_scan.generate_github_repository_evidence", generate
    )

    with pytest.raises(GitHubRepositorySourceNotFoundError):
        run_github_repository_scan(session, uuid4(), Mock(spec=GitHubProvider))

    persist.assert_not_called()
    generate.assert_not_called()
