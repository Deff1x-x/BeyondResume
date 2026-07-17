"""Create database foundation tables.

Revision ID: 20260717_0001
Revises:
Create Date: 2026-07-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260717_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", postgresql.CITEXT(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), server_default=sa.text("'active'"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint("role IN ('candidate', 'employer')", name="ck_users_role"),
        sa.CheckConstraint("status IN ('active', 'blocked', 'deleted')", name="ck_users_status"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ux_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role", "users", ["role"], unique=False)

    op.create_table(
        "candidate_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("headline", sa.String(length=160), nullable=True),
        sa.Column("country", sa.String(length=80), nullable=True),
        sa.Column("timezone", sa.String(length=60), nullable=True),
        sa.Column(
            "desired_role",
            sa.String(length=80),
            server_default=sa.text("'junior_python_backend_developer'"),
            nullable=False,
        ),
        sa.Column("work_format", sa.String(length=20), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint(
            "work_format IN ('remote', 'hybrid', 'onsite', 'any')",
            name="ck_candidate_profiles_work_format",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_candidate_profiles_user_id_users"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_candidate_profiles_user_id"),
    )

    op.create_table(
        "employer_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_name", sa.String(length=160), nullable=False),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_employer_profiles_user_id_users"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_employer_profiles_user_id"),
    )


def downgrade() -> None:
    op.drop_table("employer_profiles")
    op.drop_table("candidate_profiles")
    op.drop_index("ix_users_role", table_name="users")
    op.drop_index("ux_users_email", table_name="users")
    op.drop_table("users")
