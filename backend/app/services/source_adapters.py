from collections.abc import Iterable
from typing import Protocol


class SourceAdapter(Protocol):
    @property
    def source_type(self) -> str: ...

    def fetch(self, *args: object, **kwargs: object) -> object: ...

    def normalize(self, *args: object, **kwargs: object) -> object: ...

    def persist_snapshot(self, *args: object, **kwargs: object) -> object: ...

    def generate_evidence(self, *args: object, **kwargs: object) -> object: ...

    def run_scan(self, *args: object, **kwargs: object) -> object: ...


class DuplicateSourceAdapterError(ValueError):
    """Raised when an adapter source type has already been registered."""


class SourceAdapterNotFoundError(LookupError):
    """Raised when no adapter has been registered for a source type."""


class SourceAdapterRegistry:
    def __init__(self, adapters: Iterable[SourceAdapter] = ()) -> None:
        self._adapters: dict[str, SourceAdapter] = {}
        for adapter in adapters:
            self.register(adapter)

    def register(self, adapter: SourceAdapter) -> None:
        source_type = adapter.source_type
        if not source_type:
            raise ValueError("Source adapter type must not be empty")
        if source_type in self._adapters:
            raise DuplicateSourceAdapterError(source_type)
        self._adapters[source_type] = adapter

    def get(self, source_type: str) -> SourceAdapter:
        try:
            return self._adapters[source_type]
        except KeyError as error:
            raise SourceAdapterNotFoundError(source_type) from error
