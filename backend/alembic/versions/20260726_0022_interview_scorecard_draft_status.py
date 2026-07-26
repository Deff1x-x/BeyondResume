"""Add draft/completed status and nullable ratings for interview scorecards.

Revision ID: 20260726_0022
Revises: 20260726_0021
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260726_0022"
down_revision: Union[str, None] = "20260726_0021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "employer_interview_scorecards",
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="completed",
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_employer_interview_scorecards_status",
        "employer_interview_scorecards",
        "status IN ('draft', 'completed')",
    )

    op.drop_constraint(
        "ck_employer_interview_scorecards_technical_competency",
        "employer_interview_scorecards",
        type_="check",
    )
    op.drop_constraint(
        "ck_employer_interview_scorecards_experience_relevance",
        "employer_interview_scorecards",
        type_="check",
    )
    op.drop_constraint(
        "ck_employer_interview_scorecards_communication",
        "employer_interview_scorecards",
        type_="check",
    )
    op.drop_constraint(
        "ck_employer_interview_scorecards_ownership",
        "employer_interview_scorecards",
        type_="check",
    )
    op.drop_constraint(
        "ck_employer_interview_scorecards_recommendation",
        "employer_interview_scorecards",
        type_="check",
    )

    op.alter_column(
        "employer_interview_scorecards",
        "technical_competency",
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.alter_column(
        "employer_interview_scorecards",
        "experience_relevance",
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.alter_column(
        "employer_interview_scorecards",
        "communication",
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.alter_column(
        "employer_interview_scorecards",
        "ownership",
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.alter_column(
        "employer_interview_scorecards",
        "recommendation",
        existing_type=sa.String(length=20),
        nullable=True,
    )

    op.create_check_constraint(
        "ck_employer_interview_scorecards_technical_competency",
        "employer_interview_scorecards",
        "technical_competency IS NULL OR technical_competency BETWEEN 1 AND 5",
    )
    op.create_check_constraint(
        "ck_employer_interview_scorecards_experience_relevance",
        "employer_interview_scorecards",
        "experience_relevance IS NULL OR experience_relevance BETWEEN 1 AND 5",
    )
    op.create_check_constraint(
        "ck_employer_interview_scorecards_communication",
        "employer_interview_scorecards",
        "communication IS NULL OR communication BETWEEN 1 AND 5",
    )
    op.create_check_constraint(
        "ck_employer_interview_scorecards_ownership",
        "employer_interview_scorecards",
        "ownership IS NULL OR ownership BETWEEN 1 AND 5",
    )
    op.create_check_constraint(
        "ck_employer_interview_scorecards_recommendation",
        "employer_interview_scorecards",
        "recommendation IS NULL OR recommendation IN ('strong_yes', 'yes', 'mixed', 'no')",
    )

    # New rows default to draft; existing rows remain completed assessments.
    op.alter_column(
        "employer_interview_scorecards",
        "status",
        server_default="draft",
        existing_type=sa.String(length=20),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE employer_interview_scorecards
        SET
            technical_competency = COALESCE(technical_competency, 1),
            experience_relevance = COALESCE(experience_relevance, 1),
            communication = COALESCE(communication, 1),
            ownership = COALESCE(ownership, 1),
            recommendation = COALESCE(recommendation, 'mixed')
        """
    )

    op.drop_constraint(
        "ck_employer_interview_scorecards_technical_competency",
        "employer_interview_scorecards",
        type_="check",
    )
    op.drop_constraint(
        "ck_employer_interview_scorecards_experience_relevance",
        "employer_interview_scorecards",
        type_="check",
    )
    op.drop_constraint(
        "ck_employer_interview_scorecards_communication",
        "employer_interview_scorecards",
        type_="check",
    )
    op.drop_constraint(
        "ck_employer_interview_scorecards_ownership",
        "employer_interview_scorecards",
        type_="check",
    )
    op.drop_constraint(
        "ck_employer_interview_scorecards_recommendation",
        "employer_interview_scorecards",
        type_="check",
    )
    op.drop_constraint(
        "ck_employer_interview_scorecards_status",
        "employer_interview_scorecards",
        type_="check",
    )

    op.alter_column(
        "employer_interview_scorecards",
        "technical_competency",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.alter_column(
        "employer_interview_scorecards",
        "experience_relevance",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.alter_column(
        "employer_interview_scorecards",
        "communication",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.alter_column(
        "employer_interview_scorecards",
        "ownership",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.alter_column(
        "employer_interview_scorecards",
        "recommendation",
        existing_type=sa.String(length=20),
        nullable=False,
    )

    op.create_check_constraint(
        "ck_employer_interview_scorecards_technical_competency",
        "employer_interview_scorecards",
        "technical_competency BETWEEN 1 AND 5",
    )
    op.create_check_constraint(
        "ck_employer_interview_scorecards_experience_relevance",
        "employer_interview_scorecards",
        "experience_relevance BETWEEN 1 AND 5",
    )
    op.create_check_constraint(
        "ck_employer_interview_scorecards_communication",
        "employer_interview_scorecards",
        "communication BETWEEN 1 AND 5",
    )
    op.create_check_constraint(
        "ck_employer_interview_scorecards_ownership",
        "employer_interview_scorecards",
        "ownership BETWEEN 1 AND 5",
    )
    op.create_check_constraint(
        "ck_employer_interview_scorecards_recommendation",
        "employer_interview_scorecards",
        "recommendation IN ('strong_yes', 'yes', 'mixed', 'no')",
    )
    op.drop_column("employer_interview_scorecards", "status")
