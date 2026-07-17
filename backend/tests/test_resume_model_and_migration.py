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
