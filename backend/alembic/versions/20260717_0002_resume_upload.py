"""Create resumes table.

Revision ID: 20260717_0002
Revises: 20260717_0001
Create Date: 2026-07-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260717_0002"
down_revision: Union[str, None] = "20260717_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "resumes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_path", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("parse_status", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "parse_status IN ('uploaded', 'parsed', 'failed')",
            name="ck_resumes_parse_status",
        ),
        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["candidate_profiles.id"],
            name="fk_resumes_candidate_id_candidate_profiles",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_resumes_candidate_created", "resumes", ["candidate_id", sa.text("created_at DESC")]
    )


def downgrade() -> None:
    op.drop_index("ix_resumes_candidate_created", table_name="resumes")
    op.drop_table("resumes")
