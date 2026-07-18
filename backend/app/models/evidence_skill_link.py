import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.candidate_profile import CandidateProfile
    from app.models.evidence_unit import EvidenceUnit
    from app.models.skill import Skill


class EvidenceSkillLink(TimestampMixin, Base):
    __tablename__ = "evidence_skill_links"
    __table_args__ = (
        CheckConstraint(
            "extraction_method IN ('deterministic', 'ai', 'manual')",
            name="ck_evidence_skill_links_extraction_method",
        ),
        CheckConstraint(
            "extraction_confidence >= 0.00 AND extraction_confidence <= 1.00",
            name="ck_evidence_skill_links_extraction_confidence",
        ),
        UniqueConstraint(
            "evidence_unit_id",
            "skill_id",
            "extraction_method",
            "extraction_version",
            name="uq_evidence_skill_links_identity",
        ),
        Index("ix_evidence_skill_links_candidate_id", "candidate_id"),
        Index("ix_evidence_skill_links_skill_id", "skill_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_profiles.id"), nullable=False
    )
    evidence_unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evidence_units.id"), nullable=False
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id"), nullable=False
    )
    extraction_method: Mapped[str] = mapped_column(String(50), nullable=False)
    extraction_version: Mapped[str] = mapped_column(String(100), nullable=False)
    extraction_confidence: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    context: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)

    candidate_profile: Mapped["CandidateProfile"] = relationship(
        back_populates="evidence_skill_links"
    )
    evidence_unit: Mapped["EvidenceUnit"] = relationship(back_populates="skill_links")
    skill: Mapped["Skill"] = relationship(back_populates="evidence_skill_links")
