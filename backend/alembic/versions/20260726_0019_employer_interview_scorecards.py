"""Add employer interview scorecards.

Revision ID: 20260726_0019
Revises: 20260726_0018
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260726_0019"
down_revision: Union[str, None] = "20260726_0018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "employer_interview_scorecards",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vacancy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("technical_competency", sa.Integer(), nullable=False),
        sa.Column("experience_relevance", sa.Integer(), nullable=False),
        sa.Column("communication", sa.Integer(), nullable=False),
        sa.Column("ownership", sa.Integer(), nullable=False),
        sa.Column("interview_summary", sa.Text(), nullable=True),
        sa.Column("interview_notes", sa.Text(), nullable=True),
        sa.Column("recommendation", sa.String(length=20), nullable=False),
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
            "technical_competency BETWEEN 1 AND 5",
            name="ck_employer_interview_scorecards_technical_competency",
        ),
        sa.CheckConstraint(
            "experience_relevance BETWEEN 1 AND 5",
            name="ck_employer_interview_scorecards_experience_relevance",
        ),
        sa.CheckConstraint(
            "communication BETWEEN 1 AND 5",
            name="ck_employer_interview_scorecards_communication",
        ),
        sa.CheckConstraint(
            "ownership BETWEEN 1 AND 5",
            name="ck_employer_interview_scorecards_ownership",
        ),
        sa.CheckConstraint(
            "recommendation IN ('strong_yes', 'yes', 'mixed', 'no')",
            name="ck_employer_interview_scorecards_recommendation",
        ),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidate_profiles.id"]),
        sa.ForeignKeyConstraint(["employer_id"], ["employer_profiles.id"]),
        sa.ForeignKeyConstraint(["vacancy_id"], ["vacancies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "vacancy_id",
            "candidate_id",
            name="uq_employer_interview_scorecards_vacancy_candidate",
        ),
    )


def downgrade() -> None:
    op.drop_table("employer_interview_scorecards")
