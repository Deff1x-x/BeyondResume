import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.evidence_skill_link import EvidenceSkillLink
    from app.models.skill_alias import SkillAlias
    from app.models.vacancy_skill_requirement import VacancySkillRequirement


class Skill(TimestampMixin, Base):
    __tablename__ = "skills"
    __table_args__ = (UniqueConstraint("normalized_name", name="uq_skills_normalized_name"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    canonical_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    deprecated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ontology_version: Mapped[str] = mapped_column(String(100), nullable=False)

    aliases: Mapped[list["SkillAlias"]] = relationship(back_populates="skill")
    evidence_skill_links: Mapped[list["EvidenceSkillLink"]] = relationship(back_populates="skill")
    vacancy_skill_requirements: Mapped[list["VacancySkillRequirement"]] = relationship(
        back_populates="skill"
    )
