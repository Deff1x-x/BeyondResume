"""Add structured vacancy skill requirements.

Revision ID: 20260720_0014
Revises: 20260720_0013
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260720_0014"
down_revision: Union[str, None] = "20260720_0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vacancy_skill_requirements",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vacancy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requirement_type", sa.String(length=20), nullable=False),
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
            "requirement_type IN ('required', 'preferred')",
            name="ck_vacancy_skill_requirements_type",
        ),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"]),
        sa.ForeignKeyConstraint(["vacancy_id"], ["vacancies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "vacancy_id",
            "skill_id",
            name="uq_vacancy_skill_requirements_vacancy_skill",
        ),
    )
    op.create_index(
        "ix_vacancy_skill_requirements_vacancy_id",
        "vacancy_skill_requirements",
        ["vacancy_id"],
    )
    op.create_index(
        "ix_vacancy_skill_requirements_skill_id",
        "vacancy_skill_requirements",
        ["skill_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_vacancy_skill_requirements_skill_id",
        table_name="vacancy_skill_requirements",
    )
    op.drop_index(
        "ix_vacancy_skill_requirements_vacancy_id",
        table_name="vacancy_skill_requirements",
    )
    op.drop_table("vacancy_skill_requirements")
