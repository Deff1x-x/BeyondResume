import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class EmployerInterviewScorecard(TimestampMixin, Base):
    """Manual interviewer evaluation for one vacancy and candidate pair."""

    __tablename__ = "employer_interview_scorecards"
    __table_args__ = (
        UniqueConstraint(
            "vacancy_id",
            "candidate_id",
            name="uq_employer_interview_scorecards_vacancy_candidate",
        ),
        CheckConstraint(
            "status IN ('draft', 'completed')",
            name="ck_employer_interview_scorecards_status",
        ),
        CheckConstraint(
            "technical_competency IS NULL OR technical_competency BETWEEN 1 AND 5",
            name="ck_employer_interview_scorecards_technical_competency",
        ),
        CheckConstraint(
            "experience_relevance IS NULL OR experience_relevance BETWEEN 1 AND 5",
            name="ck_employer_interview_scorecards_experience_relevance",
        ),
        CheckConstraint(
            "communication IS NULL OR communication BETWEEN 1 AND 5",
            name="ck_employer_interview_scorecards_communication",
        ),
        CheckConstraint(
            "ownership IS NULL OR ownership BETWEEN 1 AND 5",
            name="ck_employer_interview_scorecards_ownership",
        ),
        CheckConstraint(
            "recommendation IS NULL OR recommendation IN ('strong_yes', 'yes', 'mixed', 'no')",
            name="ck_employer_interview_scorecards_recommendation",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employer_profiles.id"), nullable=False
    )
    vacancy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vacancies.id"), nullable=False
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_profiles.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    technical_competency: Mapped[int | None] = mapped_column(Integer, nullable=True)
    experience_relevance: Mapped[int | None] = mapped_column(Integer, nullable=True)
    communication: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ownership: Mapped[int | None] = mapped_column(Integer, nullable=True)
    interview_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    interview_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(String(20), nullable=True)
