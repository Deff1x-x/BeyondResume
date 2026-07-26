import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.candidate_profile import CandidateProfile
    from app.models.vacancy import Vacancy


class Application(TimestampMixin, Base):
    """Candidate application to one vacancy.

    Status is an extensible string constrained by CHECK. Only ``applied`` and
    ``withdrawn`` are used now; additional hiring statuses can widen the
    constraint later without redesigning the table.
    """

    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint(
            "vacancy_id",
            "candidate_id",
            name="uq_applications_vacancy_candidate",
        ),
        CheckConstraint(
            "status IN ('applied', 'withdrawn')",
            name="ck_applications_status",
        ),
        Index("ix_applications_vacancy_id", "vacancy_id"),
        Index("ix_applications_candidate_id", "candidate_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    vacancy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vacancies.id"), nullable=False
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_profiles.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'applied'")
    )

    vacancy: Mapped["Vacancy"] = relationship(back_populates="applications")
    candidate_profile: Mapped["CandidateProfile"] = relationship(
        back_populates="applications"
    )
