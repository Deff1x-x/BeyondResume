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
            "technical_competency BETWEEN 1 AND 5",
            name="ck_employer_interview_scorecards_technical_competency",
        ),
        CheckConstraint(
            "experience_relevance BETWEEN 1 AND 5",
            name="ck_employer_interview_scorecards_experience_relevance",
        ),
        CheckConstraint(
            "communication BETWEEN 1 AND 5",
            name="ck_employer_interview_scorecards_communication",
        ),
        CheckConstraint(
            "ownership BETWEEN 1 AND 5",
            name="ck_employer_interview_scorecards_ownership",
        ),
        CheckConstraint(
            "recommendation IN ('strong_yes', 'yes', 'mixed', 'no')",
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
    technical_competency: Mapped[int] = mapped_column(Integer, nullable=False)
    experience_relevance: Mapped[int] = mapped_column(Integer, nullable=False)
    communication: Mapped[int] = mapped_column(Integer, nullable=False)
    ownership: Mapped[int] = mapped_column(Integer, nullable=False)
    interview_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    interview_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str] = mapped_column(String(20), nullable=False)
