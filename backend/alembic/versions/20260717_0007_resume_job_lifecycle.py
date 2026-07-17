"""Add resume and job lifecycle fields.

Revision ID: 20260717_0007
Revises: 20260717_0006
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260717_0007"
down_revision: Union[str, None] = "20260717_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("jobs_resume_id_key", "jobs", type_="unique")
    op.create_index(
        "ix_jobs_active_resume",
        "jobs",
        ["resume_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('pending', 'running')"),
    )
    op.add_column("resumes", sa.Column("parsed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("resumes", sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("resumes", sa.Column("parse_error_code", sa.String(64), nullable=True))
    op.add_column("resumes", sa.Column("parse_error_message", sa.String(255), nullable=True))
    op.add_column("jobs", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("jobs", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("jobs", sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("jobs", sa.Column("error_code", sa.String(64), nullable=True))
    op.add_column("jobs", sa.Column("error_message", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("jobs", "error_message")
    op.drop_column("jobs", "error_code")
    op.drop_column("jobs", "failed_at")
    op.drop_column("jobs", "completed_at")
    op.drop_column("jobs", "started_at")
    op.drop_column("resumes", "parse_error_message")
    op.drop_column("resumes", "parse_error_code")
    op.drop_column("resumes", "failed_at")
    op.drop_column("resumes", "parsed_at")
    op.drop_index("ix_jobs_active_resume", table_name="jobs")
    op.create_unique_constraint("jobs_resume_id_key", "jobs", ["resume_id"])
