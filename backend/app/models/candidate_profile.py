import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.resume import Resume
    from app.models.user import User


class CandidateProfile(TimestampMixin, Base):
    __tablename__ = "candidate_profiles"
    __table_args__ = (
        CheckConstraint(
            "work_format IN ('remote', 'hybrid', 'onsite', 'any')",
            name="ck_candidate_profiles_work_format",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True
    )
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    headline: Mapped[str | None] = mapped_column(String(160), nullable=True)
    country: Mapped[str | None] = mapped_column(String(80), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(60), nullable=True)
    desired_role: Mapped[str] = mapped_column(
        String(80), nullable=False, server_default=text("'junior_python_backend_developer'")
    )
    work_format: Mapped[str | None] = mapped_column(String(20), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="candidate_profile")
    resumes: Mapped[list["Resume"]] = relationship(back_populates="candidate_profile")
