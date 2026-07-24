import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
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
