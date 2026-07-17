import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    desc,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.candidate_profile import CandidateProfile


class Resume(Base):
    __tablename__ = "resumes"
    __table_args__ = (
        CheckConstraint(
            "parse_status IN ('uploaded', 'parsed', 'failed')",
            name="ck_resumes_parse_status",
        ),
        Index("ix_resumes_candidate_created", "candidate_id", desc("created_at")),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_profiles.id"), nullable=False
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_current: Mapped[bool] = mapped_column(nullable=False, server_default="true")
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parse_status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    candidate_profile: Mapped["CandidateProfile"] = relationship(back_populates="resumes")

    @property
    def candidate_profile_id(self) -> uuid.UUID:
        return self.candidate_id

    @property
    def storage_path(self) -> str:
        return self.stored_path

    @property
    def file_size(self) -> int:
        return self.file_size_bytes

    @property
    def status(self) -> str:
        return self.parse_status

    @property
    def uploaded_at(self) -> datetime:
        return self.created_at
