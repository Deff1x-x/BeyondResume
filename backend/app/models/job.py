import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Index,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class JobType(str, Enum):
    RESUME_PARSE = "resume_parse"
    PROFILE_ANALYSIS = "profile_analysis"
    GITHUB_SCAN = "github_scan"
    PASSPORT_GENERATION = "passport_generation"
    VACANCY_NORMALIZATION = "vacancy_normalization"
    MATCH_CALCULATION = "match_calculation"
    ASSESSMENT_REVIEW = "assessment_review"
    ROADMAP_GENERATION = "roadmap_generation"
    EXPORT_GENERATION = "export_generation"
    WEBHOOK_DELIVERY = "webhook_delivery"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        CheckConstraint(
            "job_type != 'resume_parse' OR resume_id IS NOT NULL", name="ck_jobs_resume_context"
        ),
        Index(
            "ix_jobs_active_resume",
            "resume_id",
            unique=True,
            postgresql_where=text("status IN ('pending', 'running')"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=True
    )
    job_type: Mapped[JobType] = mapped_column(SqlEnum(JobType, name="job_type"), nullable=False)
    status: Mapped[JobStatus] = mapped_column(SqlEnum(JobStatus, name="job_status"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(255), nullable=True)
