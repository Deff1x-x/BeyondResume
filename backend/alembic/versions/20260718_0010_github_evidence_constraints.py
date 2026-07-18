"""Add GitHub evidence ownership and deduplication constraints.

Revision ID: 20260718_0010
Revises: 20260718_0009
"""

from typing import Sequence, Union

from alembic import op


revision: str = "20260718_0010"
down_revision: Union[str, None] = "20260718_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_evidence_units_ownership_status",
        "evidence_units",
        "ownership_status IN ('unverified', 'verified') OR ownership_status IS NULL",
    )
    op.create_unique_constraint(
        "uq_evidence_units_candidate_source",
        "evidence_units",
        ["candidate_id", "source_type", "source_reference"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_evidence_units_candidate_source", "evidence_units", type_="unique")
    op.drop_constraint("ck_evidence_units_ownership_status", "evidence_units", type_="check")
