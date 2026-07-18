import uuid
from decimal import Decimal
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.candidate_profile import CandidateProfile


class EvidenceUnit(TimestampMixin, Base):
    __tablename__ = "evidence_units"
    __table_args__ = (
        CheckConstraint(
            "verification_status IN ("
            "'unverified', 'source_reachable', 'ownership_confirmed', 'issuer_verified', "
            "'platform_assessed', 'disputed', 'invalidated') "
            "OR verification_status IS NULL",
            name="ck_evidence_units_verification_status",
        ),
        CheckConstraint(
            "ownership_status IN ('unverified', 'verified') OR ownership_status IS NULL",
            name="ck_evidence_units_ownership_status",
        ),
        UniqueConstraint(
            "candidate_id",
            "source_type",
            "source_reference",
            name="uq_evidence_units_candidate_source",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_profiles.id"), nullable=False
    )
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_reference: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    freshness_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ownership_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    strength_score: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    quality_flags: Mapped[dict[str, bool] | None] = mapped_column(JSONB, nullable=True)
    raw_payload_reference: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    candidate_profile: Mapped["CandidateProfile"] = relationship(back_populates="evidence_units")
