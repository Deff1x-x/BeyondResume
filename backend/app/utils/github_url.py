from dataclasses import dataclass
import re
from urllib.parse import urlsplit


class GitHubRepositoryUrlError(ValueError):
    """Raised when a public GitHub repository URL is unsafe or malformed."""


_ALLOWED_HOSTS = frozenset({"github.com", "www.github.com"})
_OWNER_PATTERN = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,37}[a-z0-9])?$")
_REPOSITORY_PATTERN = re.compile(r"[a-z0-9][a-z0-9._-]{0,99}$")


@dataclass(frozen=True, slots=True)
class GitHubRepositoryURL:
    owner: str
    repository: str
    canonical_url: str


def parse_github_repository_url(value: str) -> GitHubRepositoryURL:
    if not isinstance(value, str) or not value or any(character.isspace() for character in value):
        raise GitHubRepositoryUrlError("GitHub repository URL must not contain whitespace")
    if "\\" in value:
        raise GitHubRepositoryUrlError("GitHub repository URL must not contain backslashes")

    try:
        parsed = urlsplit(value)
    except ValueError as error:
        raise GitHubRepositoryUrlError("GitHub repository URL is malformed") from error

    if parsed.scheme.lower() != "https":
        raise GitHubRepositoryUrlError("GitHub repository URL must use HTTPS")
    if parsed.netloc.lower() not in _ALLOWED_HOSTS:
        raise GitHubRepositoryUrlError("GitHub repository URL host is not allowed")
    if parsed.query or parsed.fragment:
        raise GitHubRepositoryUrlError("GitHub repository URL must not contain query or fragment")
    if "%" in parsed.path:
        raise GitHubRepositoryUrlError("GitHub repository URL path must not be percent-encoded")

    path_parts = parsed.path.split("/")
    if len(path_parts) not in {3, 4} or path_parts[0] or (len(path_parts) == 4 and path_parts[3]):
        raise GitHubRepositoryUrlError(
            "GitHub repository URL must contain only owner and repository"
        )

    owner, repository = path_parts[1:3]
    if repository.lower().endswith(".git"):
        repository = repository[:-4]

    normalized_owner = owner.lower()
    normalized_repository = repository.lower()
    if not _is_valid_repository_identity(normalized_owner, normalized_repository):
        raise GitHubRepositoryUrlError("GitHub repository owner or name is invalid")

    return GitHubRepositoryURL(
        owner=normalized_owner,
        repository=normalized_repository,
        canonical_url=f"https://github.com/{normalized_owner}/{normalized_repository}",
    )


def is_valid_github_repository_identity(owner: str, repository: str) -> bool:
    return (
        owner == owner.lower()
        and repository == repository.lower()
        and _is_valid_repository_identity(owner, repository)
    )


def _is_valid_repository_identity(owner: str, repository: str) -> bool:
    return bool(_OWNER_PATTERN.fullmatch(owner) and _REPOSITORY_PATTERN.fullmatch(repository))
