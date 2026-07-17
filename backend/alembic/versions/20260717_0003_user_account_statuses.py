"""Align user account statuses with the specification.

Revision ID: 20260717_0003
Revises: 20260717_0002
Create Date: 2026-07-17
"""

from typing import Sequence, Union

from alembic import op

revision: str = "20260717_0003"
down_revision: Union[str, None] = "20260717_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("ck_users_status", "users", type_="check")
    op.create_check_constraint(
        "ck_users_status",
        "users",
        "status IN ('pending_verification', 'active', 'suspended', 'deletion_requested', 'deleted')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_users_status", "users", type_="check")
    op.create_check_constraint(
        "ck_users_status", "users", "status IN ('active', 'blocked', 'deleted')"
    )
