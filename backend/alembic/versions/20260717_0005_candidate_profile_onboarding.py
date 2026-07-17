"""Expand candidate profile onboarding fields.

Revision ID: 20260717_0005
Revises: 20260717_0004
Create Date: 2026-07-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260717_0005"
down_revision: Union[str, None] = "20260717_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

onboarding_status = postgresql.ENUM("profile_required", name="candidate_onboarding_status")


def upgrade() -> None:
    onboarding_status.create(op.get_bind(), checkfirst=True)
    op.drop_constraint("ck_candidate_profiles_work_format", "candidate_profiles", type_="check")
    op.alter_column(
        "candidate_profiles", "full_name", existing_type=sa.String(length=150), nullable=True
    )
    op.alter_column(
        "candidate_profiles",
        "desired_role",
        existing_type=sa.String(length=80),
        nullable=True,
        server_default=None,
    )
    op.alter_column(
        "candidate_profiles",
        "onboarding_status",
        existing_type=sa.String(length=30),
        type_=onboarding_status,
        postgresql_using="onboarding_status::candidate_onboarding_status",
    )
    op.add_column(
        "candidate_profiles", sa.Column("english_level", sa.String(length=50), nullable=True)
    )
    op.add_column(
        "candidate_profiles", sa.Column("availability", sa.String(length=100), nullable=True)
    )
    op.add_column(
        "candidate_profiles", sa.Column("data_processing_consent", sa.Boolean(), nullable=True)
    )
    op.add_column(
        "candidate_profiles", sa.Column("salary_expectation", sa.String(length=100), nullable=True)
    )
    op.add_column(
        "candidate_profiles",
        sa.Column("preferred_employment_type", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "candidate_profiles", sa.Column("relocation_readiness", sa.Boolean(), nullable=True)
    )
    op.add_column(
        "candidate_profiles", sa.Column("portfolio_url", sa.String(length=2048), nullable=True)
    )
    op.add_column(
        "candidate_profiles", sa.Column("linkedin_url", sa.String(length=2048), nullable=True)
    )


def downgrade() -> None:
    op.alter_column(
        "candidate_profiles",
        "onboarding_status",
        existing_type=onboarding_status,
        type_=sa.String(length=30),
        postgresql_using="onboarding_status::text",
    )
    op.create_check_constraint(
        "ck_candidate_profiles_work_format",
        "candidate_profiles",
        "work_format IN ('remote', 'hybrid', 'onsite', 'any')",
    )
    onboarding_status.drop(op.get_bind(), checkfirst=True)
    op.alter_column(
        "candidate_profiles",
        "desired_role",
        existing_type=sa.String(length=80),
        nullable=False,
        server_default=sa.text("'junior_python_backend_developer'"),
    )
    op.alter_column(
        "candidate_profiles", "full_name", existing_type=sa.String(length=150), nullable=False
    )
    for column in (
        "linkedin_url",
        "portfolio_url",
        "relocation_readiness",
        "preferred_employment_type",
        "salary_expectation",
        "data_processing_consent",
        "availability",
        "english_level",
    ):
        op.drop_column("candidate_profiles", column)
