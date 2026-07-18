import pytest

from app.utils.github_url import GitHubRepositoryUrlError, parse_github_repository_url


@pytest.mark.parametrize(
    ("value", "owner", "repository"),
    [
        ("https://github.com/Example-Owner/Example_Repo", "example-owner", "example_repo"),
        ("https://www.github.com/Example-Owner/Example_Repo/", "example-owner", "example_repo"),
        ("https://github.com/Example-Owner/Example_Repo.git", "example-owner", "example_repo"),
        ("https://GITHUB.COM/OWNER/REPOSITORY", "owner", "repository"),
    ],
)
def test_parse_github_repository_url_normalizes_allowed_forms(
    value: str, owner: str, repository: str
) -> None:
    result = parse_github_repository_url(value)

    assert result.owner == owner
    assert result.repository == repository
    assert result.canonical_url == f"https://github.com/{owner}/{repository}"


@pytest.mark.parametrize(
    "value",
    [
        "http://github.com/owner/repository",
        "https://user:password@github.com/owner/repository",
        "https://github.com:443/owner/repository",
        "https://github.com/owner/repository?tab=readme",
        "https://github.com/owner/repository#readme",
        "https://github.com/owner/repository/tree/main",
        "https://github.com/owner",
        "https://github.com//repository",
        "https://github.com/./repository",
        "https://github.com/../repository",
        "https://github.com/owner/.",
        "https://github.com/owner/..",
        "https://github.com/owner%2Frepository",
        "https://github.com/%2e%2e/repository",
        "https://github.com\\owner\\repository",
        "https://api.github.com/owner/repository",
        "https://github.com.evil.test/owner/repository",
        "https://evilgithub.com/owner/repository",
        "https://127.0.0.1/owner/repository",
        "https://[::1]/owner/repository",
        "https://",
        "github.com/owner/repository",
        " https://github.com/owner/repository",
        "https://github.com/owner/repository ",
        "https://github.com/owner name/repository",
    ],
)
def test_parse_github_repository_url_rejects_unsafe_or_ambiguous_values(value: str) -> None:
    with pytest.raises(GitHubRepositoryUrlError):
        parse_github_repository_url(value)
