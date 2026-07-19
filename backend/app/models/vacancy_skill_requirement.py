import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.skill import Skill
    from app.models.vacancy import Vacancy


class VacancySkillRequirement(TimestampMixin, Base):
    """Structured vacancy skill requirement linked to the Skill ontology."""

    __tablename__ = "vacancy_skill_requirements"
    __table_args__ = (
        CheckConstraint(
            "requirement_type IN ('required', 'preferred')",
            name="ck_vacancy_skill_requirements_type",
        ),
        UniqueConstraint(
            "vacancy_id",
            "skill_id",
            name="uq_vacancy_skill_requirements_vacancy_skill",
        ),
        Index("ix_vacancy_skill_requirements_vacancy_id", "vacancy_id"),
        Index("ix_vacancy_skill_requirements_skill_id", "skill_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vacancy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vacancies.id"), nullable=False
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id"), nullable=False
    )
    requirement_type: Mapped[str] = mapped_column(String(20), nullable=False)

    vacancy: Mapped["Vacancy"] = relationship(back_populates="skill_requirements")
    skill: Mapped["Skill"] = relationship(back_populates="vacancy_skill_requirements")
