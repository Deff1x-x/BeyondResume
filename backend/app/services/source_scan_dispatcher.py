from uuid import UUID

from sqlalchemy.orm import Session

from app.services.source_adapters import SourceAdapterRegistry, validate_source_type


def dispatch_source_scan(
    registry: SourceAdapterRegistry,
    source_type: str,
    *,
    session: Session,
    candidate_id: UUID,
) -> object:
    validated_source_type = validate_source_type(source_type)
    adapter = registry.get(validated_source_type)
    return adapter.run_scan(session, candidate_id)
