"""Migration contract for applications and candidate contact fields."""

from pathlib import Path


def test_application_migration_scope() -> None:
    migration_path = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "20260726_0021_applications_and_candidate_contacts.py"
    )
    source = migration_path.read_text(encoding="utf-8")

    assert 'revision: str = "20260726_0021"' in source
    assert 'down_revision: Union[str, None] = "20260726_0020"' in source
    assert 'op.create_table(\n        "applications"' in source
    assert "uq_applications_vacancy_candidate" in source
    assert "ck_applications_status" in source
    assert "status IN ('applied', 'withdrawn')" in source
    assert 'ForeignKeyConstraint(["candidate_id"], ["candidate_profiles.id"])' in source
    assert 'ForeignKeyConstraint(["vacancy_id"], ["vacancies.id"])' in source
    assert 'sa.Column("phone", sa.String(length=50), nullable=True)' in source
    assert 'sa.Column("telegram", sa.String(length=100), nullable=True)' in source
    assert 'op.drop_table("applications")' in source
    assert 'op.drop_column("candidate_profiles", "telegram")' in source
    assert 'op.drop_column("candidate_profiles", "phone")' in source
    assert "postgresql.ENUM" not in source
