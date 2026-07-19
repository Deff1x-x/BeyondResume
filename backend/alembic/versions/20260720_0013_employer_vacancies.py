"""Add employer vacancies for job postings.

Revision ID: 20260720_0013
Revises: 20260719_0012
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260720_0013"
down_revision: Union[str, None] = "20260719_0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vacancies",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="open", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("status IN ('draft', 'open', 'closed')", name="ck_vacancies_status"),
        sa.ForeignKeyConstraint(["employer_id"], ["employer_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_vacancies_employer_id", "vacancies", ["employer_id"])


def downgrade() -> None:
    op.drop_index("ix_vacancies_employer_id", table_name="vacancies")
    op.drop_table("vacancies")
