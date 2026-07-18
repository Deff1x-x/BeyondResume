"""Add skill ontology and evidence skill links.

Revision ID: 20260718_0011
Revises: 20260718_0010
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260718_0011"
down_revision: Union[str, None] = "20260718_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("canonical_name", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("deprecated", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("ontology_version", sa.String(length=100), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("normalized_name", name="uq_skills_normalized_name"),
    )
    op.create_table(
        "skill_aliases",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("alias", sa.String(length=255), nullable=False),
        sa.Column("normalized_alias", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("normalized_alias", name="uq_skill_aliases_normalized_alias"),
    )
    op.create_table(
        "evidence_skill_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evidence_unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("extraction_method", sa.String(length=50), nullable=False),
        sa.Column("extraction_version", sa.String(length=100), nullable=False),
        sa.Column("extraction_confidence", sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
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
            "extraction_method IN ('deterministic', 'ai', 'manual')",
            name="ck_evidence_skill_links_extraction_method",
        ),
        sa.CheckConstraint(
            "extraction_confidence >= 0.00 AND extraction_confidence <= 1.00",
            name="ck_evidence_skill_links_extraction_confidence",
        ),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidate_profiles.id"]),
        sa.ForeignKeyConstraint(["evidence_unit_id"], ["evidence_units.id"]),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "evidence_unit_id",
            "skill_id",
            "extraction_method",
            "extraction_version",
            name="uq_evidence_skill_links_identity",
        ),
    )
    op.create_index(
        "ix_evidence_skill_links_candidate_id", "evidence_skill_links", ["candidate_id"]
    )
    op.create_index("ix_evidence_skill_links_skill_id", "evidence_skill_links", ["skill_id"])


def downgrade() -> None:
    op.drop_index("ix_evidence_skill_links_skill_id", table_name="evidence_skill_links")
    op.drop_index("ix_evidence_skill_links_candidate_id", table_name="evidence_skill_links")
    op.drop_table("evidence_skill_links")
    op.drop_table("skill_aliases")
    op.drop_table("skills")
