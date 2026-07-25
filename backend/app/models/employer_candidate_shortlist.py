import uuid

from sqlalchemy import CheckConstraint, ForeignKey, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class EmployerCandidateShortlist(TimestampMixin, Base):
    """A candidate explicitly saved by an employer for one owned vacancy."""

    __tablename__ = "employer_candidate_shortlists"
    __table_args__ = (
        UniqueConstraint(
            "vacancy_id",
            "candidate_id",
            name="uq_employer_candidate_shortlists_vacancy_candidate",
        ),
        CheckConstraint(
            "stage IN ("
            "'shortlisted', 'screening', 'interview', 'offer', 'hired', 'rejected'"
            ")",
            name="ck_employer_candidate_shortlists_stage",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    employer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employer_profiles.id"), nullable=False
    )
    vacancy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vacancies.id"), nullable=False
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_profiles.id"), nullable=False
    )
    stage: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'shortlisted'")
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
