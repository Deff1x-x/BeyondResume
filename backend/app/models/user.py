import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Index, String, Text, text
from sqlalchemy.dialects.postgresql import CITEXT, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.candidate_profile import CandidateProfile
    from app.models.employer_profile import EmployerProfile


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('candidate', 'employer')", name="ck_users_role"),
        CheckConstraint(
            "status IN ('pending_verification', 'active', 'suspended', "
            "'deletion_requested', 'deleted')",
            name="ck_users_status",
        ),
        Index("ux_users_email", "email", unique=True),
        Index("ix_users_role", "role"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(CITEXT, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'active'"))

    candidate_profile: Mapped["CandidateProfile | None"] = relationship(
        back_populates="user", uselist=False
    )
    employer_profile: Mapped["EmployerProfile | None"] = relationship(
        back_populates="user", uselist=False
    )
