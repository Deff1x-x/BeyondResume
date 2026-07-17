import importlib.util
from pathlib import Path

from sqlalchemy import CheckConstraint

from app.db.base import Base
import app.models  # noqa: F401


def test_resume_metadata_matches_contract() -> None:
    resumes = Base.metadata.tables["resumes"]

    assert set(resumes.columns.keys()) == {
        "id",
        "candidate_id",
        "original_filename",
        "stored_path",
        "mime_type",
        "file_size_bytes",
        "extracted_text",
        "parse_status",
        "created_at",
        "checksum",
        "is_current",
        "parsed_at",
        "failed_at",
        "parse_error_code",
        "parse_error_message",
    }
    assert "updated_at" not in resumes.columns
    assert {foreign_key.target_fullname for foreign_key in resumes.c.candidate_id.foreign_keys} == {
        "candidate_profiles.id"
    }
    assert "ck_resumes_parse_status" in {
        constraint.name
        for constraint in resumes.constraints
        if isinstance(constraint, CheckConstraint)
    }
    assert "ix_resumes_candidate_created" in {index.name for index in resumes.indexes}


def test_resume_migration_scope() -> None:
    migration_path = (
        Path(__file__).parents[1] / "alembic" / "versions" / "20260717_0002_resume_upload.py"
    )
    spec = importlib.util.spec_from_file_location("resume_upload_migration", migration_path)

    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    source = migration_path.read_text(encoding="utf-8")
    assert module.revision == "20260717_0002"
    assert module.down_revision == "20260717_0001"
    assert 'op.create_table(\n        "resumes"' in source
    assert 'op.create_index(\n        "ix_resumes_candidate_created"' in source
    assert 'op.drop_index("ix_resumes_candidate_created"' in source
    assert 'op.drop_table("resumes")' in source


def test_resume_job_lifecycle_migration_scope() -> None:
    migration_path = (
        Path(__file__).parents[1] / "alembic" / "versions" / "20260717_0007_resume_job_lifecycle.py"
    )
    source = migration_path.read_text(encoding="utf-8")

    assert 'revision: str = "20260717_0007"' in source
    assert 'down_revision: Union[str, None] = "20260717_0006"' in source
    assert 'op.create_index(\n        "ix_jobs_active_resume"' in source
    assert "status IN ('pending', 'running')" in source
    assert 'op.add_column("resumes", sa.Column("parsed_at"' in source
    assert 'op.add_column("jobs", sa.Column("started_at"' in source
    assert 'op.drop_index("ix_jobs_active_resume", table_name="jobs")' in source


def test_job_enum_migration_creates_each_postgresql_type_once() -> None:
    migration_path = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "20260717_0006_resume_upload_infrastructure.py"
    )
    source = migration_path.read_text(encoding="utf-8")

    # The explicit create is retained for PostgreSQL; create_type=False prevents
    # op.create_table() from emitting each ENUM a second time in offline SQL.
    assert source.count("create_type=False") == 2
    assert source.count("job_type.create(") == 1
    assert source.count("job_status.create(") == 1


def test_active_resume_job_index_is_partial_and_resume_scoped() -> None:
    jobs = Base.metadata.tables["jobs"]
    index = next(index for index in jobs.indexes if index.name == "ix_jobs_active_resume")

    assert index.unique is True
    assert list(index.columns.keys()) == ["resume_id"]
    assert "pending" in str(index.dialect_options["postgresql"]["where"])
    assert "running" in str(index.dialect_options["postgresql"]["where"])
    for terminal_status in ("completed", "failed", "cancelled", "expired"):
        assert terminal_status not in str(index.dialect_options["postgresql"]["where"])
