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
