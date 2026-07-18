from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.integrations.github import GitHubProvider
from app.services.github_full_scan import GitHubRepositoryScanResult
from app.services.github_source_adapter import GitHubSourceAdapter
from app.services.source_adapters import (
    DuplicateSourceAdapterError,
    SourceAdapterNotFoundError,
    SourceAdapterRegistry,
)


class FakeSourceAdapter:
    def __init__(self, source_type: str) -> None:
        self.source_type = source_type

    def fetch(self) -> object:
        return object()

    def normalize(self) -> object:
        return object()

    def persist_snapshot(self) -> object:
        return object()

    def generate_evidence(self) -> object:
        return object()

    def run_scan(self) -> object:
        return object()


def test_registry_registers_and_returns_same_adapter_instance() -> None:
    registry = SourceAdapterRegistry()
    adapter = FakeSourceAdapter("example_source")

    registry.register(adapter)

    assert registry.get("example_source") is adapter


def test_registry_rejects_duplicate_source_type() -> None:
    registry = SourceAdapterRegistry([FakeSourceAdapter("example_source")])

    with pytest.raises(DuplicateSourceAdapterError):
        registry.register(FakeSourceAdapter("example_source"))


def test_registry_rejects_empty_source_type_and_missing_adapter() -> None:
    registry = SourceAdapterRegistry()

    with pytest.raises(ValueError, match="must not be empty"):
        registry.register(FakeSourceAdapter(""))
    with pytest.raises(SourceAdapterNotFoundError):
        registry.get("missing_source")


def test_github_adapter_can_be_registered() -> None:
    adapter = GitHubSourceAdapter(Mock(spec=GitHubProvider))
    registry = SourceAdapterRegistry([adapter])

    assert adapter.source_type == "github_repository"
    assert registry.get("github_repository") is adapter


def test_github_adapter_delegates_orchestration(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = Mock(spec=GitHubProvider)
    adapter = GitHubSourceAdapter(provider)
    session = Mock()
    candidate_id = uuid4()
    result = Mock(spec=GitHubRepositoryScanResult)
    run_scan = Mock(return_value=result)
    monkeypatch.setattr("app.services.github_source_adapter.run_github_repository_scan", run_scan)

    assert adapter.run_scan(session, candidate_id) is result
    run_scan.assert_called_once_with(session, candidate_id, provider)
