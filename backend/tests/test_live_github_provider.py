import base64

import pytest

from app.integrations.github import (
    DemoGitHubProvider,
    GitHubAuthenticationError,
    GitHubRateLimitError,
    GitHubRepositoryNotFoundError,
    LiveGitHubProvider,
    get_github_provider,
)
from app.utils.github_url import parse_github_repository_url


def test_live_provider_builds_pipeline_compatible_snapshot_from_mocked_api() -> None:
    prefix = "https://api.github.com/repos/deff1x-x/beyondresume"
    responses: dict[str, object] = {
        prefix: {"default_branch": "main", "description": "Public", "private": False, "archived": False},
        f"{prefix}/branches/main": {"commit": {"sha": "abc123"}},
        f"{prefix}/git/trees/abc123?recursive=1": {"tree": [{"path": "README.md", "type": "blob"}, {"path": "pyproject.toml", "type": "blob"}, {"path": "app/main.py", "type": "blob"}]},
        f"{prefix}/contents/pyproject.toml?ref=abc123": _content("[project]\ndependencies = []\n"),
        f"{prefix}/contents/app/main.py?ref=abc123": _content("from fastapi import FastAPI\napp = FastAPI()\n"),
        f"{prefix}/languages": {"Python": 10, "TypeScript": 5},
        f"{prefix}/readme": _content("# BeyondResume\n"),
    }
    snapshot = LiveGitHubProvider(request_json=responses.__getitem__).get_repository_snapshot(
        parse_github_repository_url("https://github.com/deff1x-x/beyondresume")
    )
    assert snapshot.is_demo is False
    assert snapshot.canonical_url == "https://github.com/deff1x-x/beyondresume"
    assert snapshot.default_branch == "main"
    assert snapshot.languages == ("Python", "TypeScript")
    assert snapshot.file_tree == ("README.md", "app/main.py", "pyproject.toml")
    assert snapshot.manifest_paths == ("pyproject.toml",)
    assert snapshot.readme_text == "# BeyondResume\n"
    assert snapshot.normalized_manifests[0].path == "pyproject.toml"
    assert snapshot.source_files == (("app/main.py", "from fastapi import FastAPI\napp = FastAPI()\n"),)


def test_provider_selection_uses_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.integrations.github.settings.github_provider", "live")
    assert isinstance(get_github_provider(), LiveGitHubProvider)
    monkeypatch.setattr("app.integrations.github.settings.github_provider", "demo")
    assert isinstance(get_github_provider(), DemoGitHubProvider)


@pytest.mark.parametrize("status,error_type", [(404, GitHubRepositoryNotFoundError), (401, GitHubAuthenticationError), (429, GitHubRateLimitError)])
def test_live_provider_maps_http_errors(monkeypatch: pytest.MonkeyPatch, status: int, error_type: type[Exception]) -> None:
    from urllib.error import HTTPError
    def fail(*_args: object, **_kwargs: object) -> object:
        raise HTTPError("https://api.github.com/repos/example/repo", status, "error", {"X-RateLimit-Remaining": "0"}, None)
    monkeypatch.setattr("app.integrations.github.urlopen", fail)
    with pytest.raises(error_type):
        LiveGitHubProvider()._get_json("https://api.github.com/repos/example/repo")


def _content(value: str) -> dict[str, str]:
    return {"encoding": "base64", "content": base64.b64encode(value.encode()).decode()}
