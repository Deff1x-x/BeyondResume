import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.career_companion_action_skill import CareerCompanionActionSkill
    from app.models.career_companion_plan import CareerCompanionPlan
    from app.models.github_repository import GitHubRepository


class CareerCompanionAction(TimestampMixin, Base):
    __tablename__ = "career_companion_actions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_companion_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    horizon: Mapped[str] = mapped_column(String(30), nullable=False)
    action_type: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="suggested")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    why_it_matters: Mapped[str] = mapped_column(Text, nullable=False, default="")
    implementation_steps: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    expected_artifacts: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    verification_method: Mapped[str] = mapped_column(Text, nullable=False, default="")
    estimated_effort: Mapped[str] = mapped_column(String(40), nullable=False, default="medium")
    github_repository_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("github_repositories.id", ondelete="SET NULL"),
        nullable=True,
    )
    project_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    current_target_impact: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    career_growth_impact: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    priority_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    priority_explanation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    plan: Mapped["CareerCompanionPlan"] = relationship(back_populates="actions")
    github_repository: Mapped["GitHubRepository | None"] = relationship()
    skills: Mapped[list["CareerCompanionActionSkill"]] = relationship(
        back_populates="action", cascade="all, delete-orphan"
    )
