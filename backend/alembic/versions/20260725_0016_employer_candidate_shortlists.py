"""Add employer candidate shortlists.

Revision ID: 20260725_0016
Revises: 20260721_0015
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260725_0016"
down_revision: Union[str, None] = "20260721_0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "employer_candidate_shortlists",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vacancy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
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
        sa.ForeignKeyConstraint(["candidate_id"], ["candidate_profiles.id"]),
        sa.ForeignKeyConstraint(["employer_id"], ["employer_profiles.id"]),
        sa.ForeignKeyConstraint(["vacancy_id"], ["vacancies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "vacancy_id",
            "candidate_id",
            name="uq_employer_candidate_shortlists_vacancy_candidate",
        ),
    )


def downgrade() -> None:
    op.drop_table("employer_candidate_shortlists")
