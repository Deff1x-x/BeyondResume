from dataclasses import replace
from unittest.mock import Mock
from uuid import UUID, uuid4
import socket

import pytest

from app.integrations.github import (
    DemoGitHubProvider,
    GitHubProvider,
    GitHubRepositoryNotFoundError,
    GitHubRepositorySnapshot,
)
from app.models.candidate_profile import CandidateProfile, OnboardingStatus
from app.models.evidence_unit import EvidenceUnit
from app.models.github_repository import GitHubRepository
from app.services.candidate import CandidateProfileNotFoundError
from app.services.github_scan import (
    GitHubRepositorySourceNotFoundError,
    GitHubSnapshotIdentityMismatchError,
    fetch_github_repository_snapshot,
)
from app.utils.github_url import GitHubRepositoryUrlError


def make_candidate(candidate_id: UUID | None = None) -> CandidateProfile:
    return CandidateProfile(
        id=candidate_id or uuid4(),
        user_id=uuid4(),
        display_name="Demo Candidate",
        onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
    )


def make_repository(
    candidate_id: UUID, repository_url: str = "https://github.com/demo-user/demo-api"
) -> GitHubRepository:
    return GitHubRepository(candidate_id=candidate_id, repository_url=repository_url)


def make_snapshot() -> GitHubRepositorySnapshot:
    return GitHubRepositorySnapshot(
        canonical_url="https://github.com/demo-user/demo-api",
        repository_name="demo-api",
        owner="demo-user",
        description="Demo repository",
        default_branch="main",
        is_public=True,
        is_archived=False,
        languages=("Python",),
        file_tree=("README.md", "pyproject.toml"),
        readme_text="Demo",
        manifest_paths=("pyproject.toml",),
        is_demo=True,
    )


def make_session(candidate: CandidateProfile | None, repository: GitHubRepository | None) -> Mock:
    session = Mock()
    candidate_result = Mock()
    candidate_result.scalar_one_or_none.return_value = candidate
    repository_result = Mock()
    repository_result.scalar_one_or_none.return_value = repository
    session.execute.side_effect = [candidate_result, repository_result]
    return session


def test_fetch_returns_validated_snapshot_and_passes_normalized_repository_to_provider() -> None:
    candidate = make_candidate()
    repository = make_repository(candidate.id, "https://www.github.com/Demo-User/Demo-API.git/")
    session = make_session(candidate, repository)
    provider = Mock(spec=GitHubProvider)
    provider.get_repository_snapshot.return_value = make_snapshot()

    result = fetch_github_repository_snapshot(session, candidate.id, provider)

    assert result == make_snapshot()
    provider.get_repository_snapshot.assert_called_once()
    parsed_repository = provider.get_repository_snapshot.call_args.args[0]
    assert parsed_repository.owner == "demo-user"
    assert parsed_repository.repository == "demo-api"
    assert parsed_repository.canonical_url == "https://github.com/demo-user/demo-api"
    _assert_read_only(session)


def test_fetch_rejects_missing_candidate_without_calling_provider() -> None:
    session = Mock()
    candidate_result = Mock()
    candidate_result.scalar_one_or_none.return_value = None
    session.execute.return_value = candidate_result
    provider = Mock(spec=GitHubProvider)

    with pytest.raises(CandidateProfileNotFoundError):
        fetch_github_repository_snapshot(session, uuid4(), provider)

    provider.get_repository_snapshot.assert_not_called()
    _assert_read_only(session)


def test_fetch_rejects_missing_repository_without_calling_provider() -> None:
    candidate = make_candidate()
    session = make_session(candidate, None)
    provider = Mock(spec=GitHubProvider)

    with pytest.raises(GitHubRepositorySourceNotFoundError):
        fetch_github_repository_snapshot(session, candidate.id, provider)

    provider.get_repository_snapshot.assert_not_called()
    _assert_read_only(session)


def test_fetch_rejects_corrupted_repository_url_without_calling_provider() -> None:
    candidate = make_candidate()
    session = make_session(
        candidate, make_repository(candidate.id, "http://github.com/demo-user/demo-api")
    )
    provider = Mock(spec=GitHubProvider)

    with pytest.raises(GitHubRepositoryUrlError):
        fetch_github_repository_snapshot(session, candidate.id, provider)

    provider.get_repository_snapshot.assert_not_called()
    _assert_read_only(session)


def test_fetch_propagates_provider_error() -> None:
    candidate = make_candidate()
    session = make_session(candidate, make_repository(candidate.id))
    provider = Mock(spec=GitHubProvider)
    provider.get_repository_snapshot.side_effect = GitHubRepositoryNotFoundError

    with pytest.raises(GitHubRepositoryNotFoundError):
        fetch_github_repository_snapshot(session, candidate.id, provider)

    provider.get_repository_snapshot.assert_called_once()
    _assert_read_only(session)


@pytest.mark.parametrize(
    "snapshot",
    [
        replace(make_snapshot(), owner="other-owner"),
        replace(make_snapshot(), repository_name="other-repository"),
        replace(make_snapshot(), canonical_url="https://github.com/other-owner/demo-api"),
    ],
)
def test_fetch_rejects_provider_identity_mismatch_without_mutating_models(
    snapshot: GitHubRepositorySnapshot,
) -> None:
    candidate = make_candidate()
    repository = make_repository(candidate.id)
    session = make_session(candidate, repository)
    provider = Mock(spec=GitHubProvider)
    provider.get_repository_snapshot.return_value = snapshot

    with pytest.raises(GitHubSnapshotIdentityMismatchError):
        fetch_github_repository_snapshot(session, candidate.id, provider)

    assert repository.repository_url == "https://github.com/demo-user/demo-api"
    provider.get_repository_snapshot.assert_called_once()
    _assert_read_only(session)


def test_fetch_is_deterministic_for_same_provider_snapshot() -> None:
    candidate = make_candidate()
    snapshot = make_snapshot()
    provider = Mock(spec=GitHubProvider)
    provider.get_repository_snapshot.return_value = snapshot

    first_result = fetch_github_repository_snapshot(
        make_session(candidate, make_repository(candidate.id)), candidate.id, provider
    )
    second_result = fetch_github_repository_snapshot(
        make_session(candidate, make_repository(candidate.id)), candidate.id, provider
    )

    assert first_result == second_result == snapshot
    assert provider.get_repository_snapshot.call_count == 2


def test_fetch_uses_demo_provider_without_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_network(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("Snapshot fetch service must not use network")

    monkeypatch.setattr(socket, "create_connection", fail_network)
    candidate = make_candidate()
    session = make_session(candidate, make_repository(candidate.id))

    snapshot = fetch_github_repository_snapshot(session, candidate.id, DemoGitHubProvider())

    assert snapshot.is_demo is True
    assert snapshot.canonical_url == "https://github.com/demo-user/demo-api"
    _assert_read_only(session)


def _assert_read_only(session: Mock) -> None:
    session.add.assert_not_called()
    session.flush.assert_not_called()
    session.commit.assert_not_called()
    session.rollback.assert_not_called()
    added_models = [call.args[0] for call in session.add.call_args_list]
    assert not any(isinstance(model, EvidenceUnit) for model in added_models)
