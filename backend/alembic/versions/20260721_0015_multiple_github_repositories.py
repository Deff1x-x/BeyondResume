"""Allow multiple normalized GitHub repositories per candidate."""

from alembic import op

revision = "20260721_0015"
down_revision = "20260720_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("uq_github_repositories_candidate_id", "github_repositories", type_="unique")
    op.create_unique_constraint("uq_github_repositories_candidate_url", "github_repositories", ["candidate_id", "repository_url"])


def downgrade() -> None:
    op.drop_constraint("uq_github_repositories_candidate_url", "github_repositories", type_="unique")
    op.create_unique_constraint("uq_github_repositories_candidate_id", "github_repositories", ["candidate_id"])
