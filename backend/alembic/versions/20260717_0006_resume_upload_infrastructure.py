"""Add resume upload metadata and pending jobs.

Revision ID: 20260717_0006
Revises: 20260717_0005
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260717_0006"
down_revision: Union[str, None] = "20260717_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    job_type = postgresql.ENUM(
        "resume_parse",
        "profile_analysis",
        "github_scan",
        "passport_generation",
        "vacancy_normalization",
        "match_calculation",
        "assessment_review",
        "roadmap_generation",
        "export_generation",
        "webhook_delivery",
        name="job_type",
        create_type=False,
    )
    job_status = postgresql.ENUM(
        "pending",
        "running",
        "completed",
        "failed",
        "cancelled",
        "expired",
        name="job_status",
        create_type=False,
    )
    job_type.create(op.get_bind(), checkfirst=True)
    job_status.create(op.get_bind(), checkfirst=True)
    op.add_column("resumes", sa.Column("checksum", sa.String(length=64), nullable=True))
    op.add_column(
        "resumes",
        sa.Column("is_current", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    )
    op.create_index(
        "ix_resumes_current",
        "resumes",
        ["candidate_id"],
        unique=True,
        postgresql_where=sa.text("is_current"),
    )
    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("job_type", job_type, nullable=False),
        sa.Column("status", job_status, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "job_type != 'resume_parse' OR resume_id IS NOT NULL", name="ck_jobs_resume_context"
        ),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("resume_id"),
    )


def downgrade() -> None:
    op.drop_table("jobs")
    op.drop_index("ix_resumes_current", table_name="resumes")
    op.drop_column("resumes", "is_current")
    op.drop_column("resumes", "checksum")
    postgresql.ENUM(name="job_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="job_type").drop(op.get_bind(), checkfirst=True)
