import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.candidate_profile import CandidateProfile
    from app.models.career_companion_action import CareerCompanionAction
    from app.models.career_companion_chat_message import CareerCompanionChatMessage
    from app.models.career_companion_progress_event import CareerCompanionProgressEvent
    from app.models.vacancy import Vacancy


class CareerCompanionPlan(TimestampMixin, Base):
    __tablename__ = "career_companion_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mode: Mapped[str] = mapped_column(String(40), nullable=False)
    target_vacancy_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vacancies.id", ondelete="SET NULL"), nullable=True
    )
    target_role: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    generation_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="fallback")
    context_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    summary: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    current_position: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    candidate_profile: Mapped["CandidateProfile"] = relationship()
    target_vacancy: Mapped["Vacancy | None"] = relationship()
    actions: Mapped[list["CareerCompanionAction"]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="CareerCompanionAction.sort_order",
    )
    progress_events: Mapped[list["CareerCompanionProgressEvent"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan"
    )
    chat_messages: Mapped[list["CareerCompanionChatMessage"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan"
    )
