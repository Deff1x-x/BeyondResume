"""Add AI Career Companion persistence tables.

Revision ID: 20260726_0020
Revises: 20260726_0019
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260726_0020"
down_revision: Union[str, None] = "20260726_0019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "career_companion_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mode", sa.String(length=40), nullable=False),
        sa.Column("target_vacancy_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("target_role", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
        sa.Column(
            "generation_mode", sa.String(length=20), nullable=False, server_default="fallback"
        ),
        sa.Column("context_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "summary",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "current_position",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
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
            "mode IN ('target_vacancy', 'target_role', 'career_growth', 'explore_direction')",
            name="ck_career_companion_plans_mode",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'archived')",
            name="ck_career_companion_plans_status",
        ),
        sa.CheckConstraint(
            "generation_mode IN ('live', 'mock', 'fallback')",
            name="ck_career_companion_plans_generation_mode",
        ),
        sa.ForeignKeyConstraint(
            ["candidate_id"], ["candidate_profiles.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["target_vacancy_id"], ["vacancies.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_career_companion_plans_candidate_id",
        "career_companion_plans",
        ["candidate_id"],
    )
    op.create_index(
        "uq_career_companion_plans_one_active_per_candidate",
        "career_companion_plans",
        ["candidate_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )

    op.create_table(
        "career_companion_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("horizon", sa.String(length=30), nullable=False),
        sa.Column("action_type", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="suggested"),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("why_it_matters", sa.Text(), nullable=False),
        sa.Column(
            "implementation_steps",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "expected_artifacts",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("verification_method", sa.Text(), nullable=False),
        sa.Column("estimated_effort", sa.String(length=40), nullable=False),
        sa.Column("github_repository_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("project_label", sa.String(length=255), nullable=True),
        sa.Column(
            "current_target_impact",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "career_growth_impact",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("priority_score", sa.Float(), nullable=False),
        sa.Column("priority_explanation", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
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
            "horizon IN ('fix_now', 'build_next', 'grow_further')",
            name="ck_career_companion_actions_horizon",
        ),
        sa.CheckConstraint(
            "action_type IN ('improve_existing_project', 'build_new_project', 'learn_foundation')",
            name="ck_career_companion_actions_type",
        ),
        sa.CheckConstraint(
            "status IN ("
            "'suggested', 'accepted', 'in_progress', 'awaiting_evidence', "
            "'evidence_detected', 'partially_verified', 'completed', 'dismissed')",
            name="ck_career_companion_actions_status",
        ),
        sa.ForeignKeyConstraint(
            ["github_repository_id"],
            ["github_repositories.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"], ["career_companion_plans.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_career_companion_actions_plan_id",
        "career_companion_actions",
        ["plan_id"],
    )

    op.create_table(
        "career_companion_action_skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_name", sa.String(length=120), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False),
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
            "role IN ('gap', 'potential_cover', 'related')",
            name="ck_career_companion_action_skills_role",
        ),
        sa.ForeignKeyConstraint(
            ["action_id"], ["career_companion_actions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "action_id",
            "skill_id",
            "role",
            name="uq_career_companion_action_skill_role",
        ),
    )
    op.create_index(
        "ix_career_companion_action_skills_action_id",
        "career_companion_action_skills",
        ["action_id"],
    )

    op.create_table(
        "career_companion_progress_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
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
        sa.ForeignKeyConstraint(
            ["plan_id"], ["career_companion_plans.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_career_companion_progress_events_plan_id",
        "career_companion_progress_events",
        ["plan_id"],
    )

    op.create_table(
        "career_companion_chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("revision_applied", sa.String(length=80), nullable=True),
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
            "role IN ('user', 'assistant', 'system')",
            name="ck_career_companion_chat_messages_role",
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"], ["career_companion_plans.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_career_companion_chat_messages_plan_id",
        "career_companion_chat_messages",
        ["plan_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_career_companion_chat_messages_plan_id",
        table_name="career_companion_chat_messages",
    )
    op.drop_table("career_companion_chat_messages")
    op.drop_index(
        "ix_career_companion_progress_events_plan_id",
        table_name="career_companion_progress_events",
    )
    op.drop_table("career_companion_progress_events")
    op.drop_index(
        "ix_career_companion_action_skills_action_id",
        table_name="career_companion_action_skills",
    )
    op.drop_table("career_companion_action_skills")
    op.drop_index("ix_career_companion_actions_plan_id", table_name="career_companion_actions")
    op.drop_table("career_companion_actions")
    op.drop_index(
        "uq_career_companion_plans_one_active_per_candidate",
        table_name="career_companion_plans",
        postgresql_where=sa.text("status = 'active'"),
    )
    op.drop_index("ix_career_companion_plans_candidate_id", table_name="career_companion_plans")
    op.drop_table("career_companion_plans")
