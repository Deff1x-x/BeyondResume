"""Migration contract for employer interview scorecards."""

from pathlib import Path


def test_interview_scorecard_migration_scope() -> None:
    migration_path = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "20260726_0019_employer_interview_scorecards.py"
    )
    source = migration_path.read_text(encoding="utf-8")

    assert 'revision: str = "20260726_0019"' in source
    assert 'down_revision: Union[str, None] = "20260726_0018"' in source
    assert 'op.create_table(\n        "employer_interview_scorecards"' in source
    assert "uq_employer_interview_scorecards_vacancy_candidate" in source
    assert "ck_employer_interview_scorecards_technical_competency" in source
    assert "ck_employer_interview_scorecards_experience_relevance" in source
    assert "ck_employer_interview_scorecards_communication" in source
    assert "ck_employer_interview_scorecards_ownership" in source
    assert "ck_employer_interview_scorecards_recommendation" in source
    assert 'ForeignKeyConstraint(["candidate_id"], ["candidate_profiles.id"])' in source
    assert 'ForeignKeyConstraint(["employer_id"], ["employer_profiles.id"])' in source
    assert 'ForeignKeyConstraint(["vacancy_id"], ["vacancies.id"])' in source
    assert 'sa.Column("interview_summary", sa.Text(), nullable=True)' in source
    assert 'sa.Column("interview_notes", sa.Text(), nullable=True)' in source
    assert 'op.drop_table("employer_interview_scorecards")' in source
    assert "employer_candidate_shortlists" not in source
    assert "postgresql.ENUM" not in source
    assert "op.alter_table" not in source


def test_interview_scorecard_draft_status_migration_scope() -> None:
    migration_path = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "20260726_0022_interview_scorecard_draft_status.py"
    )
    source = migration_path.read_text(encoding="utf-8")

    assert 'revision: str = "20260726_0022"' in source
    assert 'down_revision: Union[str, None] = "20260726_0021"' in source
    # Adds the draft/completed status column with a check constraint.
    assert 'sa.Column(\n            "status"' in source
    assert "ck_employer_interview_scorecards_status" in source
    assert "status IN ('draft', 'completed')" in source
    # Ratings and recommendation become nullable for drafts.
    assert "technical_competency IS NULL OR technical_competency BETWEEN 1 AND 5" in source
    assert "experience_relevance IS NULL OR experience_relevance BETWEEN 1 AND 5" in source
    assert "communication IS NULL OR communication BETWEEN 1 AND 5" in source
    assert "ownership IS NULL OR ownership BETWEEN 1 AND 5" in source
    assert (
        "recommendation IS NULL OR recommendation IN ('strong_yes', 'yes', 'mixed', 'no')"
        in source
    )
    assert 'op.drop_column("employer_interview_scorecards", "status")' in source
    # Scoped to the scorecards table only.
    assert "employer_candidate_shortlists" not in source
    assert "create_table" not in source
    assert "postgresql.ENUM" not in source
