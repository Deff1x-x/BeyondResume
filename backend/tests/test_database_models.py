from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from app.db.base import Base
import app.models  # noqa: F401


def test_metadata_contains_database_foundation_tables() -> None:
    assert {"users", "candidate_profiles", "employer_profiles"} <= set(Base.metadata.tables)


def test_users_constraints_indexes_and_citext() -> None:
    users = Base.metadata.tables["users"]
    constraints = {constraint.name for constraint in users.constraints}
    indexes = {index.name for index in users.indexes}
    ddl = str(CreateTable(users).compile(dialect=postgresql.dialect()))

    assert {"ck_users_role", "ck_users_status"} <= constraints
    assert {"ux_users_email", "ix_users_role"} <= indexes
    assert "CITEXT" in ddl


def test_candidate_profile_user_relationship_constraints() -> None:
    table = Base.metadata.tables["candidate_profiles"]

    assert table.c.user_id.unique is True
    assert {foreign_key.target_fullname for foreign_key in table.c.user_id.foreign_keys} == {"users.id"}


def test_employer_profile_user_relationship_constraints() -> None:
    table = Base.metadata.tables["employer_profiles"]

    assert table.c.user_id.unique is True
    assert {foreign_key.target_fullname for foreign_key in table.c.user_id.foreign_keys} == {"users.id"}


def test_metadata_has_no_duplicate_unique_objects() -> None:
    users = Base.metadata.tables["users"]
    candidate_profiles = Base.metadata.tables["candidate_profiles"]
    employer_profiles = Base.metadata.tables["employer_profiles"]

    assert not [
        constraint
        for constraint in users.constraints
        if isinstance(constraint, UniqueConstraint) and list(constraint.columns.keys()) == ["email"]
    ]
    assert [
        index.name
        for index in users.indexes
        if index.unique and list(index.columns.keys()) == ["email"]
    ] == ["ux_users_email"]

    for table in (candidate_profiles, employer_profiles):
        unique_constraints = [
            constraint
            for constraint in table.constraints
            if isinstance(constraint, UniqueConstraint)
            and list(constraint.columns.keys()) == ["user_id"]
        ]
        unique_indexes = [
            index
            for index in table.indexes
            if index.unique and list(index.columns.keys()) == ["user_id"]
        ]

        assert len(unique_constraints) == 1
        assert not unique_indexes
