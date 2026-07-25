"""Add private note to employer candidate shortlists.

Revision ID: 20260726_0018
Revises: 20260726_0017
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260726_0018"
down_revision: Union[str, None] = "20260726_0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "employer_candidate_shortlists",
        sa.Column("note", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("employer_candidate_shortlists", "note")
