"""Add hiring stage to employer candidate shortlists.

Revision ID: 20260726_0017
Revises: 20260725_0016
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260726_0017"
down_revision: Union[str, None] = "20260725_0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "employer_candidate_shortlists",
        sa.Column(
            "stage",
            sa.String(length=20),
            server_default=sa.text("'shortlisted'"),
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_employer_candidate_shortlists_stage",
        "employer_candidate_shortlists",
        "stage IN ("
        "'shortlisted', 'screening', 'interview', 'offer', 'hired', 'rejected'"
        ")",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_employer_candidate_shortlists_stage",
        "employer_candidate_shortlists",
        type_="check",
    )
    op.drop_column("employer_candidate_shortlists", "stage")
