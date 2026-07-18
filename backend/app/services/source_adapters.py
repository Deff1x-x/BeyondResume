from collections.abc import Iterable
from typing import Protocol
from uuid import UUID

from sqlalchemy.orm import Session


class SourceAdapter(Protocol):
    @property
    def source_type(self) -> str: ...

    def fetch(self, *args: object, **kwargs: object) -> object: ...

    def normalize(self, *args: object, **kwargs: object) -> object: ...

    def persist_snapshot(self, *args: object, **kwargs: object) -> object: ...

    def generate_evidence(self, *args: object, **kwargs: object) -> object: ...

    def run_scan(self, session: Session, candidate_id: UUID) -> object: ...


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
        source_type = validate_source_type(adapter.source_type)
        if source_type in self._adapters:
            raise DuplicateSourceAdapterError(source_type)
        self._adapters[source_type] = adapter

    def get(self, source_type: str) -> SourceAdapter:
        source_type = validate_source_type(source_type)
        try:
            return self._adapters[source_type]
        except KeyError as error:
            raise SourceAdapterNotFoundError(source_type) from error


def validate_source_type(source_type: str) -> str:
    if not isinstance(source_type, str) or not source_type:
        raise ValueError("Source adapter type must be a non-empty string")
    return source_type
