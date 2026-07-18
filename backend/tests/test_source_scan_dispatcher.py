from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.integrations.github import GitHubProvider
from app.services.github_source_adapter import GitHubSourceAdapter
from app.services.source_adapters import SourceAdapterNotFoundError, SourceAdapterRegistry
from app.services.source_scan_dispatcher import dispatch_source_scan


class FakeSourceAdapter:
    def __init__(self, source_type: str, result: object | None = None) -> None:
        self.source_type = source_type
        self.result = result if result is not None else object()
        self.run_scan = Mock(return_value=self.result)

    def fetch(self, *_args: object, **_kwargs: object) -> object:
        return object()

    def normalize(self, *_args: object, **_kwargs: object) -> object:
        return object()

    def persist_snapshot(self, *_args: object, **_kwargs: object) -> object:
        return object()

    def generate_evidence(self, *_args: object, **_kwargs: object) -> object:
        return object()


def test_dispatcher_calls_matching_adapter_once_and_returns_same_result() -> None:
    expected_result = object()
    adapter = FakeSourceAdapter("first_source", expected_result)
    other_adapter = FakeSourceAdapter("other_source")
    registry = SourceAdapterRegistry([adapter, other_adapter])
    session = Mock()
    candidate_id = uuid4()

    result = dispatch_source_scan(
        registry, "first_source", session=session, candidate_id=candidate_id
    )

    assert result is expected_result
    adapter.run_scan.assert_called_once_with(session, candidate_id)
    other_adapter.run_scan.assert_not_called()
    session.commit.assert_not_called()
    session.rollback.assert_not_called()
    session.flush.assert_not_called()
    session.close.assert_not_called()
    session.begin.assert_not_called()


def test_dispatcher_uses_one_registry_lookup_without_registry_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = FakeSourceAdapter("example_source")
    registry = SourceAdapterRegistry([adapter])
    get = Mock(wraps=registry.get)
    monkeypatch.setattr(registry, "get", get)

    dispatch_source_scan(registry, "example_source", session=Mock(), candidate_id=uuid4())

    get.assert_called_once_with("example_source")
    assert registry.get("example_source") is adapter


def test_dispatcher_propagates_missing_adapter_without_calling_any_adapter() -> None:
    adapter = FakeSourceAdapter("registered_source")
    registry = SourceAdapterRegistry([adapter])

    with pytest.raises(SourceAdapterNotFoundError):
        dispatch_source_scan(registry, "missing_source", session=Mock(), candidate_id=uuid4())

    adapter.run_scan.assert_not_called()


def test_dispatcher_propagates_adapter_error_without_retry_or_fallback() -> None:
    error = RuntimeError("source scan failed")
    failing_adapter = FakeSourceAdapter("failing_source")
    failing_adapter.run_scan.side_effect = error
    other_adapter = FakeSourceAdapter("other_source")
    registry = SourceAdapterRegistry([failing_adapter, other_adapter])

    with pytest.raises(RuntimeError, match="source scan failed"):
        dispatch_source_scan(registry, "failing_source", session=Mock(), candidate_id=uuid4())

    failing_adapter.run_scan.assert_called_once()
    other_adapter.run_scan.assert_not_called()


@pytest.mark.parametrize("source_type", ["", 42])
def test_dispatcher_rejects_invalid_source_type_before_lookup(source_type: object) -> None:
    registry = Mock(spec=SourceAdapterRegistry)

    with pytest.raises(ValueError, match="non-empty string"):
        dispatch_source_scan(registry, source_type, session=Mock(), candidate_id=uuid4())  # type: ignore[arg-type]

    registry.get.assert_not_called()


def test_github_adapter_delegates_through_dispatcher(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = GitHubSourceAdapter(Mock(spec=GitHubProvider))
    registry = SourceAdapterRegistry([adapter])
    session = Mock()
    candidate_id = uuid4()
    expected_result = object()
    run_scan = Mock(return_value=expected_result)
    monkeypatch.setattr(adapter, "run_scan", run_scan)

    assert (
        dispatch_source_scan(
            registry, "github_repository", session=session, candidate_id=candidate_id
        )
        is expected_result
    )
    run_scan.assert_called_once_with(session, candidate_id)
