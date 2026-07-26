"""Add applications table and candidate contact fields.

Revision ID: 20260726_0021
Revises: 20260726_0020
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260726_0021"
down_revision: Union[str, None] = "20260726_0020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vacancy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="applied",
            nullable=False,
        ),
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
        sa.CheckConstraint(
            "status IN ('applied', 'withdrawn')",
            name="ck_applications_status",
        ),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidate_profiles.id"]),
        sa.ForeignKeyConstraint(["vacancy_id"], ["vacancies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "vacancy_id",
            "candidate_id",
            name="uq_applications_vacancy_candidate",
        ),
    )
    op.create_index(
        "ix_applications_vacancy_id", "applications", ["vacancy_id"], unique=False
    )
    op.create_index(
        "ix_applications_candidate_id", "applications", ["candidate_id"], unique=False
    )
    op.add_column(
        "candidate_profiles", sa.Column("phone", sa.String(length=50), nullable=True)
    )
    op.add_column(
        "candidate_profiles", sa.Column("telegram", sa.String(length=100), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("candidate_profiles", "telegram")
    op.drop_column("candidate_profiles", "phone")
    op.drop_index("ix_applications_candidate_id", table_name="applications")
    op.drop_index("ix_applications_vacancy_id", table_name="applications")
    op.drop_table("applications")
