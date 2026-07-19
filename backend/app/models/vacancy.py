import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.employer_profile import EmployerProfile
    from app.models.vacancy_skill_requirement import VacancySkillRequirement


class Vacancy(TimestampMixin, Base):
    """Employer job posting. Distinct from the background ``Job`` engine table."""

    __tablename__ = "vacancies"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'open', 'closed')",
            name="ck_vacancies_status",
        ),
        Index("ix_vacancies_employer_id", "employer_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employer_profiles.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'open'")
    )

    employer_profile: Mapped["EmployerProfile"] = relationship(back_populates="vacancies")
    skill_requirements: Mapped[list["VacancySkillRequirement"]] = relationship(
        back_populates="vacancy"
    )
