import importlib.util
from pathlib import Path


def test_database_foundation_migration_imports() -> None:
    migration_path = (
        Path(__file__).parents[1] / "alembic" / "versions" / "20260717_0001_database_foundation.py"
    )
    spec = importlib.util.spec_from_file_location("database_foundation_migration", migration_path)

    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.revision == "20260717_0001"


def test_database_foundation_migration_has_no_duplicate_unique_objects() -> None:
    migration_path = (
        Path(__file__).parents[1] / "alembic" / "versions" / "20260717_0001_database_foundation.py"
    )
    source = migration_path.read_text(encoding="utf-8")

    assert source.count('op.create_index("ux_users_email"') == 1
    assert 'sa.UniqueConstraint("email"' not in source
    assert source.count('sa.UniqueConstraint("user_id"') == 2


def test_user_account_status_migration_follows_resume_migration() -> None:
    migration_path = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "20260717_0003_user_account_statuses.py"
    )
    source = migration_path.read_text(encoding="utf-8")

    assert 'down_revision: Union[str, None] = "20260717_0002"' in source
    for account_status in (
        "pending_verification",
        "active",
        "suspended",
        "deletion_requested",
        "deleted",
    ):
        assert account_status in source


def test_registration_workflow_migration_follows_account_status_migration() -> None:
    migration_path = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "20260717_0004_registration_workflow.py"
    )
    source = migration_path.read_text(encoding="utf-8")

    assert 'down_revision: Union[str, None] = "20260717_0003"' in source
    assert "onboarding_status" in source
    assert "profile_required" in source
    assert "audit_events" in source


def test_candidate_profile_onboarding_migration_follows_registration_workflow() -> None:
    migration_path = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "20260717_0005_candidate_profile_onboarding.py"
    )
    source = migration_path.read_text(encoding="utf-8")

    assert 'down_revision: Union[str, None] = "20260717_0004"' in source
    assert "candidate_onboarding_status" in source
    assert "english_level" in source
    assert "data_processing_consent" in source
    assert "op.drop_column" in source
