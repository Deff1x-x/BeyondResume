import json
from pathlib import Path
import socket

import pytest

from app.integrations.github import (
    MAX_FILE_TREE_PATHS,
    MAX_README_CHARS,
    DemoGitHubProvider,
    GitHubFixtureError,
    GitHubRepositoryIdentityError,
    GitHubRepositoryNotFoundError,
)
from app.utils.github_url import GitHubRepositoryURL, parse_github_repository_url


def test_demo_provider_reads_fixture_without_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_network(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("Demo provider must not use network")

    monkeypatch.setattr(socket, "create_connection", fail_network)
    provider = DemoGitHubProvider()

    snapshot = provider.get_repository_snapshot(
        parse_github_repository_url("https://github.com/demo-user/demo-api")
    )

    assert snapshot.is_demo is True
    assert snapshot.canonical_url == "https://github.com/demo-user/demo-api"
    assert snapshot.languages == ("Python", "SQL")
    assert snapshot.manifest_paths == ("pyproject.toml",)
    assert not hasattr(snapshot, "commits")
    assert not hasattr(snapshot, "pull_requests")
    assert not hasattr(snapshot, "issues")


def test_demo_provider_returns_deterministic_snapshot() -> None:
    provider = DemoGitHubProvider()
    repository = parse_github_repository_url("https://github.com/demo-user/demo-api")

    assert provider.get_repository_snapshot(repository) == provider.get_repository_snapshot(
        repository
    )


def test_demo_provider_rejects_unknown_fixture() -> None:
    provider = DemoGitHubProvider()

    with pytest.raises(GitHubRepositoryNotFoundError):
        provider.get_repository_snapshot(
            parse_github_repository_url("https://github.com/demo-user/missing")
        )


def test_demo_provider_rejects_non_normalized_identity_before_building_path() -> None:
    provider = DemoGitHubProvider()
    unsafe_repository = GitHubRepositoryURL(
        owner="../fixtures",
        repository="demo-api",
        canonical_url="https://github.com/../fixtures/demo-api",
    )

    with pytest.raises(GitHubRepositoryIdentityError):
        provider.get_repository_snapshot(unsafe_repository)


@pytest.mark.parametrize(
    "field,value",
    [
        ("readme_text", "x" * (MAX_README_CHARS + 1)),
        ("file_tree", [f"src/{index}.py" for index in range(MAX_FILE_TREE_PATHS + 1)]),
        ("commits", []),
    ],
)
def test_demo_provider_rejects_malformed_or_unbounded_fixture(
    tmp_path: Path, field: str, value: object
) -> None:
    fixture = _valid_fixture()
    fixture[field] = value
    _write_fixture(tmp_path, fixture)

    with pytest.raises(GitHubFixtureError):
        DemoGitHubProvider(tmp_path).get_repository_snapshot(
            parse_github_repository_url("https://github.com/demo-user/demo-api")
        )


def test_demo_provider_rejects_invalid_json_fixture(tmp_path: Path) -> None:
    (tmp_path / "demo-user--demo-api.json").write_text("{not-json", encoding="utf-8")

    with pytest.raises(GitHubFixtureError):
        DemoGitHubProvider(tmp_path).get_repository_snapshot(
            parse_github_repository_url("https://github.com/demo-user/demo-api")
        )


def _valid_fixture() -> dict[str, object]:
    return {
        "canonical_url": "https://github.com/demo-user/demo-api",
        "repository_name": "demo-api",
        "owner": "demo-user",
        "description": "Fixture",
        "default_branch": "main",
        "is_public": True,
        "is_archived": False,
        "languages": ["Python"],
        "file_tree": ["README.md", "pyproject.toml"],
        "readme_text": "Fixture README",
        "manifest_paths": ["pyproject.toml"],
    }


def _write_fixture(directory: Path, fixture: dict[str, object]) -> None:
    (directory / "demo-user--demo-api.json").write_text(json.dumps(fixture), encoding="utf-8")
