"""Typed source-consistency error contract for future GitHub re-extraction."""


class GitHubEvidenceSourceConsistencyError(Exception):
    """Raised when persisted GitHub source entities are mutually inconsistent."""
