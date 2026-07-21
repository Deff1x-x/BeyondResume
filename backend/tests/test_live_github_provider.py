import base64
from io import BytesIO
import tarfile

import pytest

from app.integrations.github import (
    DemoGitHubProvider,
    GitHubAuthenticationError,
    GitHubRateLimitError,
    GitHubRepositoryNotFoundError,
    LiveGitHubProvider,
    MAX_ANONYMOUS_SOURCE_FILES,
    MAX_SOURCE_FILES,
    _prioritize_source_paths,
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
    snapshot = LiveGitHubProvider(
        request_json=responses.__getitem__,
        request_bytes=lambda _url: _archive({"README.md": "# BeyondResume\n", "pyproject.toml": "[project]\ndependencies = []\n", "app/main.py": "from fastapi import FastAPI\napp = FastAPI()\n"}),
    ).get_repository_snapshot(
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


def test_live_provider_bounds_source_requests_below_unauthenticated_api_limit() -> None:
    prefix = "https://api.github.com/repos/demo/project"
    manifest_paths = tuple(f"packages/{index}/package.json" for index in range(50))
    source_paths = tuple(f"src/{index}.py" for index in range(60))
    responses: dict[str, object] = {
        prefix: {"default_branch": "main", "description": None, "private": False, "archived": False},
        f"{prefix}/branches/main": {"commit": {"sha": "abc123"}},
        f"{prefix}/git/trees/abc123?recursive=1": {
            "tree": [
                *({"path": path, "type": "blob"} for path in manifest_paths),
                *({"path": path, "type": "blob"} for path in source_paths),
            ]
        },
        f"{prefix}/languages": {"Python": 1},
        f"{prefix}/readme": _content("# Demo\n"),
    }
    responses.update(
        {f"{prefix}/contents/{path}?ref=abc123": _content("{}") for path in manifest_paths}
    )
    responses.update(
        {f"{prefix}/contents/{path}?ref=abc123": _content("print('ok')\n") for path in source_paths}
    )
    requested: list[str] = []

    def request_json(url: str) -> object:
        requested.append(url)
        return responses[url]

    snapshot = LiveGitHubProvider(
        request_json=request_json,
        request_bytes=lambda _url: _archive({**{path: "{}" for path in manifest_paths}, **{path: "print('ok')\n" for path in source_paths}}),
    ).get_repository_snapshot(
        parse_github_repository_url("https://github.com/demo/project")
    )

    assert len(snapshot.source_files) == MAX_SOURCE_FILES
    assert len(requested) == 4
    assert len(requested) < 60
    assert not any("/contents/" in url for url in requested)


def test_live_provider_uses_bearer_token_without_logging_it(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    token = "secret-token"

    class Response:
        status = 200
        headers = {"X-RateLimit-Remaining": "4999"}

        def read(self) -> bytes:
            return b"{}"

        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

    def fake_urlopen(request, **_kwargs):
        assert request.get_header("Authorization") == f"Bearer {token}"
        return Response()

    monkeypatch.setattr("app.integrations.github.urlopen", fake_urlopen)
    with caplog.at_level("INFO", logger="app.integrations.github"):
        assert LiveGitHubProvider(token=token)._get_json("https://api.github.com/repos/demo/project") == {}

    assert token not in caplog.text


def test_source_budget_is_dynamic_for_anonymous_and_normal_for_authenticated() -> None:
    anonymous = LiveGitHubProvider()
    anonymous._rate_limit_remaining = 4
    assert anonymous._source_request_budget() == 3
    anonymous._rate_limit_remaining = 100
    assert anonymous._source_request_budget() == MAX_ANONYMOUS_SOURCE_FILES

    authenticated = LiveGitHubProvider(token="token")
    authenticated._rate_limit_remaining = 0
    assert authenticated._source_request_budget() == MAX_SOURCE_FILES


def test_archive_preserves_manifest_and_source_snapshot() -> None:
    prefix = "https://api.github.com/repos/demo/project"
    responses: dict[str, object] = {
        prefix: {"default_branch": "main", "description": None, "private": False, "archived": False},
        f"{prefix}/branches/main": {"commit": {"sha": "abc123"}},
        f"{prefix}/git/trees/abc123?recursive=1": {
            "tree": [
                {"path": "package.json", "type": "blob"},
                {"path": "app/main.py", "type": "blob"},
            ]
        },
        f"{prefix}/languages": {"Python": 1},
        f"{prefix}/readme": _content("# Demo\n"),
    }
    provider = LiveGitHubProvider(token="token", request_json=responses.__getitem__, request_bytes=lambda _url: _archive({"package.json": "{}", "app/main.py": "print('ok')\n"}))
    snapshot = provider.get_repository_snapshot(parse_github_repository_url("https://github.com/demo/project"))

    assert len(snapshot.normalized_manifests) == 1
    assert snapshot.source_files == (("app/main.py", "print('ok')\n"),)


def test_source_priority_is_deterministic_and_prefers_ci_config_and_tests() -> None:
    paths = (
        "src/feature.py",
        "README.md",
        "app/main.py",
        "Dockerfile",
        ".github/workflows/test.yml",
        "tests/test_api.py",
        "package.json",
    )

    assert _prioritize_source_paths(paths) == (
        ".github/workflows/test.yml",
        "Dockerfile",
        "tests/test_api.py",
        "app/main.py",
        "src/feature.py",
    )


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


def _archive(files: dict[str, str]) -> bytes:
    buffer = BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for path, content in files.items():
            data = content.encode()
            info = tarfile.TarInfo(f"repository-sha/{path}")
            info.size = len(data)
            tar.addfile(info, BytesIO(data))
    return buffer.getvalue()
