import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.career_companion_action import CareerCompanionAction
    from app.models.skill import Skill


class CareerCompanionActionSkill(TimestampMixin, Base):
    __tablename__ = "career_companion_action_skills"
    __table_args__ = (
        UniqueConstraint("action_id", "skill_id", "role", name="uq_career_companion_action_skill_role"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_companion_actions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False
    )
    skill_name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False)

    action: Mapped["CareerCompanionAction"] = relationship(back_populates="skills")
    skill: Mapped["Skill"] = relationship()
