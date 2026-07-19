"""Add universal owner and subject context to jobs.

Revision ID: 20260719_0012
Revises: 20260718_0011
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260719_0012"
down_revision: Union[str, None] = "20260718_0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("jobs", sa.Column("subject_type", sa.String(50), nullable=True))
    op.add_column("jobs", sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_jobs_candidate_id", "jobs", "candidate_profiles", ["candidate_id"], ["id"]
    )
    op.create_index(
        "ix_jobs_active_subject",
        "jobs",
        ["subject_type", "subject_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('pending', 'running')"),
    )
    op.create_check_constraint(
        "ck_jobs_subject_pair",
        "jobs",
        "(subject_type IS NULL) = (subject_id IS NULL)",
    )
    op.create_check_constraint(
        "ck_jobs_github_scan_context",
        "jobs",
        "job_type != 'github_scan' OR ("
        "candidate_id IS NOT NULL AND subject_type IS NOT NULL AND subject_id IS NOT NULL"
        ")",
    )


def downgrade() -> None:
    op.drop_constraint("ck_jobs_github_scan_context", "jobs", type_="check")
    op.drop_constraint("ck_jobs_subject_pair", "jobs", type_="check")
    op.drop_index("ix_jobs_active_subject", table_name="jobs")
    op.drop_constraint("fk_jobs_candidate_id", "jobs", type_="foreignkey")
    op.drop_column("jobs", "subject_id")
    op.drop_column("jobs", "subject_type")
    op.drop_column("jobs", "candidate_id")
