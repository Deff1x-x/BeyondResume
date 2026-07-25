from collections.abc import Callable, Generator
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.dependencies import require_employer
from app.db.session import engine, get_db
from app.main import app
from app.models.candidate_profile import CandidateProfile, OnboardingStatus
from app.models.employer_candidate_shortlist import EmployerCandidateShortlist
from app.models.employer_profile import EmployerProfile
from app.models.user import User
from app.models.vacancy import Vacancy


@dataclass(frozen=True)
class ShortlistContext:
    employer_user: User
    employer: EmployerProfile
    other_employer: EmployerProfile
    vacancy: Vacancy
    second_vacancy: Vacancy
    foreign_vacancy: Vacancy
    candidate_ids: tuple[UUID, UUID, UUID]
    foreign_entry_id: UUID
    new_session: Callable[[], Session]


@pytest.fixture
def shortlist_client() -> Generator[tuple[TestClient, ShortlistContext], None, None]:
    try:
        connection = engine.connect()
    except SQLAlchemyError as error:
        pytest.skip(f"PostgreSQL is unavailable: {error}")

    transaction = connection.begin()
    setup = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )
    employer_user = User(
        id=uuid4(),
        email=f"shortlist-employer-{uuid4()}@example.com",
        password_hash="hash",
        role="employer",
        status="active",
    )
    other_employer_user = User(
        id=uuid4(),
        email=f"shortlist-other-{uuid4()}@example.com",
        password_hash="hash",
        role="employer",
        status="active",
    )
    employer = EmployerProfile(
        id=uuid4(), user_id=employer_user.id, company_name="Shortlist Employer"
    )
    other_employer = EmployerProfile(
        id=uuid4(), user_id=other_employer_user.id, company_name="Other Employer"
    )
    vacancy = Vacancy(
        id=uuid4(), employer_id=employer.id, title="Backend Engineer", status="open"
    )
    second_vacancy = Vacancy(
        id=uuid4(), employer_id=employer.id, title="Platform Engineer", status="open"
    )
    foreign_vacancy = Vacancy(
        id=uuid4(), employer_id=other_employer.id, title="Foreign Vacancy", status="open"
    )
    candidate_users = [
        User(
            id=uuid4(),
            email=f"shortlist-candidate-{uuid4()}@example.com",
            password_hash="hash",
            role="candidate",
            status="active",
        )
        for _ in range(3)
    ]
    candidates = [
        CandidateProfile(
            id=uuid4(),
            user_id=user.id,
            display_name=f"Candidate {index}",
            onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
        )
        for index, user in enumerate(candidate_users, start=1)
    ]
    foreign_entry = EmployerCandidateShortlist(
        id=uuid4(),
        employer_id=other_employer.id,
        vacancy_id=foreign_vacancy.id,
        candidate_id=candidates[0].id,
    )
    setup.add_all(
        [
            employer_user,
            other_employer_user,
            *candidate_users,
            employer,
            other_employer,
            vacancy,
            second_vacancy,
            foreign_vacancy,
            *candidates,
        ]
    )
    setup.flush()
    setup.add(foreign_entry)
    setup.commit()
    setup.close()

    def new_session() -> Session:
        return Session(bind=connection, join_transaction_mode="create_savepoint")

    context = ShortlistContext(
        employer_user=employer_user,
        employer=employer,
        other_employer=other_employer,
        vacancy=vacancy,
        second_vacancy=second_vacancy,
        foreign_vacancy=foreign_vacancy,
        candidate_ids=(candidates[0].id, candidates[1].id, candidates[2].id),
        foreign_entry_id=foreign_entry.id,
        new_session=new_session,
    )

    def request_session() -> Generator[Session, None, None]:
        session = new_session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = request_session
    app.dependency_overrides[require_employer] = lambda: employer_user
    try:
        with TestClient(app) as client:
            yield client, context
    finally:
        app.dependency_overrides.clear()
        transaction.rollback()
        connection.close()


def _put(client: TestClient, vacancy_id: UUID, candidate_id: UUID):
    return client.put(
        f"/api/v1/employer/vacancies/{vacancy_id}/shortlist/{candidate_id}"
    )


def _patch(client: TestClient, vacancy_id: UUID, candidate_id: UUID, stage: str, **extra):
    body: dict[str, object] = {"stage": stage, **extra}
    return client.patch(
        f"/api/v1/employer/vacancies/{vacancy_id}/shortlist/{candidate_id}",
        json=body,
    )


def _patch_note(
    client: TestClient,
    vacancy_id: UUID,
    candidate_id: UUID,
    body: dict[str, object],
):
    return client.patch(
        f"/api/v1/employer/vacancies/{vacancy_id}/shortlist/{candidate_id}/note",
        json=body,
    )


def _delete(client: TestClient, vacancy_id: UUID, candidate_id: UUID):
    return client.delete(
        f"/api/v1/employer/vacancies/{vacancy_id}/shortlist/{candidate_id}"
    )


def _get(client: TestClient, vacancy_id: UUID):
    return client.get(f"/api/v1/employer/vacancies/{vacancy_id}/shortlist")


SHORTLIST_RESPONSE_KEYS = {
    "id",
    "vacancy_id",
    "candidate_id",
    "stage",
    "note",
    "created_at",
    "updated_at",
}

ALL_STAGES = (
    "shortlisted",
    "screening",
    "interview",
    "offer",
    "hired",
    "rejected",
)

def test_save_is_idempotent_and_persists_across_requests(
    shortlist_client: tuple[TestClient, ShortlistContext],
) -> None:
    client, context = shortlist_client
    candidate_id = context.candidate_ids[0]

    first = _put(client, context.vacancy.id, candidate_id)
    second = _put(client, context.vacancy.id, candidate_id)
    persisted = _get(client, context.vacancy.id)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["stage"] == "shortlisted"
    assert first.json()["note"] is None
    assert "employer_id" not in first.json()
    assert set(first.json()) == SHORTLIST_RESPONSE_KEYS
    assert first.json()["vacancy_id"] == str(context.vacancy.id)
    assert first.json()["candidate_id"] == str(candidate_id)
    assert persisted.status_code == 200
    assert persisted.json()["entries"] == [first.json()]
    assert all("employer_id" not in entry for entry in persisted.json()["entries"])
    assert all(entry["stage"] == "shortlisted" for entry in persisted.json()["entries"])
    assert all(entry["note"] is None for entry in persisted.json()["entries"])


def test_save_rejects_missing_candidate_and_non_candidate_identifier(
    shortlist_client: tuple[TestClient, ShortlistContext],
) -> None:
    client, context = shortlist_client

    missing = _put(client, context.vacancy.id, uuid4())
    employer_account = _put(
        client, context.vacancy.id, context.employer_user.id
    )

    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "CANDIDATE_NOT_FOUND"
    assert employer_account.status_code == 404
    assert employer_account.json()["error"]["code"] == "CANDIDATE_NOT_FOUND"
    assert _get(client, context.vacancy.id).json() == {"entries": []}


def test_foreign_vacancy_shortlist_is_not_disclosed_or_mutated(
    shortlist_client: tuple[TestClient, ShortlistContext],
) -> None:
    client, context = shortlist_client
    candidate_id = context.candidate_ids[0]
    missing_candidate_id = uuid4()

    save_known = _put(client, context.foreign_vacancy.id, candidate_id)
    save_missing = _put(client, context.foreign_vacancy.id, missing_candidate_id)
    listing = _get(client, context.foreign_vacancy.id)
    removal = _delete(client, context.foreign_vacancy.id, candidate_id)
    stage_change = _patch(
        client, context.foreign_vacancy.id, candidate_id, "interview"
    )
    stage_missing = _patch(
        client, context.foreign_vacancy.id, missing_candidate_id, "interview"
    )

    for response in (
        save_known,
        save_missing,
        listing,
        removal,
        stage_change,
        stage_missing,
    ):
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "VACANCY_NOT_FOUND"

    session = context.new_session()
    try:
        foreign_entry = session.get(EmployerCandidateShortlist, context.foreign_entry_id)
        assert foreign_entry is not None
        assert foreign_entry.stage == "shortlisted"
    finally:
        session.close()


def test_delete_is_idempotent_and_does_not_remove_other_entries(
    shortlist_client: tuple[TestClient, ShortlistContext],
) -> None:
    client, context = shortlist_client
    first_candidate, second_candidate, _ = context.candidate_ids
    assert _put(client, context.vacancy.id, first_candidate).status_code == 200
    second_entry = _put(client, context.vacancy.id, second_candidate).json()

    first_delete = _delete(client, context.vacancy.id, first_candidate)
    repeated_delete = _delete(client, context.vacancy.id, first_candidate)
    listing = _get(client, context.vacancy.id)

    assert first_delete.status_code == 204
    assert first_delete.content == b""
    assert repeated_delete.status_code == 204
    assert repeated_delete.content == b""
    assert listing.json()["entries"] == [second_entry]


def test_list_is_vacancy_scoped_and_newest_first_with_id_tiebreaker(
    shortlist_client: tuple[TestClient, ShortlistContext],
) -> None:
    client, context = shortlist_client
    first_candidate, second_candidate, third_candidate = context.candidate_ids
    timestamp = datetime(2026, 7, 25, tzinfo=UTC)
    low_id = UUID(int=1)
    high_id = UUID(int=2)

    session = context.new_session()
    try:
        session.add_all(
            [
                EmployerCandidateShortlist(
                    id=low_id,
                    employer_id=context.employer.id,
                    vacancy_id=context.vacancy.id,
                    candidate_id=first_candidate,
                    created_at=timestamp,
                    updated_at=timestamp,
                ),
                EmployerCandidateShortlist(
                    id=high_id,
                    employer_id=context.employer.id,
                    vacancy_id=context.vacancy.id,
                    candidate_id=second_candidate,
                    created_at=timestamp,
                    updated_at=timestamp,
                ),
                EmployerCandidateShortlist(
                    id=uuid4(),
                    employer_id=context.employer.id,
                    vacancy_id=context.second_vacancy.id,
                    candidate_id=third_candidate,
                    created_at=timestamp,
                    updated_at=timestamp,
                ),
            ]
        )
        session.commit()
    finally:
        session.close()

    response = _get(client, context.vacancy.id)

    assert response.status_code == 200
    entries = response.json()["entries"]
    assert [entry["id"] for entry in entries] == [str(high_id), str(low_id)]
    assert all(entry["vacancy_id"] == str(context.vacancy.id) for entry in entries)
    assert all(entry["stage"] == "shortlisted" for entry in entries)
    assert all("employer_id" not in entry for entry in entries)


def test_same_candidate_can_be_saved_for_two_owned_vacancies(
    shortlist_client: tuple[TestClient, ShortlistContext],
) -> None:
    client, context = shortlist_client
    candidate_id = context.candidate_ids[0]

    first = _put(client, context.vacancy.id, candidate_id)
    second = _put(client, context.second_vacancy.id, candidate_id)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] != second.json()["id"]
    assert len(_get(client, context.vacancy.id).json()["entries"]) == 1
    assert len(_get(client, context.second_vacancy.id).json()["entries"]) == 1


def test_repeated_save_creates_only_one_database_row(
    shortlist_client: tuple[TestClient, ShortlistContext],
) -> None:
    client, context = shortlist_client
    candidate_id = context.candidate_ids[0]
    assert _put(client, context.vacancy.id, candidate_id).status_code == 200
    assert _put(client, context.vacancy.id, candidate_id).status_code == 200

    session = context.new_session()
    try:
        count = session.scalar(
            select(func.count())
            .select_from(EmployerCandidateShortlist)
            .where(
                EmployerCandidateShortlist.vacancy_id == context.vacancy.id,
                EmployerCandidateShortlist.candidate_id == candidate_id,
            )
        )
    finally:
        session.close()

    assert count == 1


def test_patch_supports_every_valid_stage_and_persists(
    shortlist_client: tuple[TestClient, ShortlistContext],
) -> None:
    client, context = shortlist_client
    candidate_id = context.candidate_ids[0]
    assert _put(client, context.vacancy.id, candidate_id).status_code == 200

    for stage in ALL_STAGES:
        response = _patch(client, context.vacancy.id, candidate_id, stage)
        assert response.status_code == 200
        assert response.json()["stage"] == stage
        assert set(response.json()) == SHORTLIST_RESPONSE_KEYS
        assert "employer_id" not in response.json()

        session = context.new_session()
        try:
            entry = session.execute(
                select(EmployerCandidateShortlist).where(
                    EmployerCandidateShortlist.vacancy_id == context.vacancy.id,
                    EmployerCandidateShortlist.candidate_id == candidate_id,
                )
            ).scalar_one()
            assert entry.stage == stage
        finally:
            session.close()


def test_same_stage_patch_is_idempotent_and_does_not_change_updated_at(
    shortlist_client: tuple[TestClient, ShortlistContext],
) -> None:
    client, context = shortlist_client
    candidate_id = context.candidate_ids[0]
    created = _put(client, context.vacancy.id, candidate_id).json()
    moved = _patch(client, context.vacancy.id, candidate_id, "interview").json()
    repeated = _patch(client, context.vacancy.id, candidate_id, "interview")

    assert repeated.status_code == 200
    assert repeated.json()["id"] == moved["id"] == created["id"]
    assert repeated.json()["stage"] == "interview"
    assert repeated.json()["updated_at"] == moved["updated_at"]
    assert repeated.json()["created_at"] == created["created_at"]

    session = context.new_session()
    try:
        count = session.scalar(
            select(func.count())
            .select_from(EmployerCandidateShortlist)
            .where(
                EmployerCandidateShortlist.vacancy_id == context.vacancy.id,
                EmployerCandidateShortlist.candidate_id == candidate_id,
            )
        )
    finally:
        session.close()
    assert count == 1


def test_real_stage_change_updates_updated_at(
    shortlist_client: tuple[TestClient, ShortlistContext],
) -> None:
    client, context = shortlist_client
    candidate_id = context.candidate_ids[0]
    created = _put(client, context.vacancy.id, candidate_id).json()
    controlled_updated_at = datetime(2026, 1, 1, tzinfo=UTC)

    session = context.new_session()
    try:
        session.execute(
            update(EmployerCandidateShortlist)
            .where(
                EmployerCandidateShortlist.vacancy_id == context.vacancy.id,
                EmployerCandidateShortlist.candidate_id == candidate_id,
            )
            .values(updated_at=controlled_updated_at)
        )
        session.commit()
    finally:
        session.close()

    changed = _patch(client, context.vacancy.id, candidate_id, "offer")
    assert changed.status_code == 200
    assert changed.json()["stage"] == "offer"
    assert changed.json()["created_at"] == created["created_at"]
    assert changed.json()["updated_at"] != controlled_updated_at.isoformat().replace(
        "+00:00", "Z"
    )
    assert changed.json()["updated_at"] != "2026-01-01T00:00:00+00:00"
    assert changed.json()["updated_at"] != "2026-01-01T00:00:00Z"

    session = context.new_session()
    try:
        entry = session.execute(
            select(EmployerCandidateShortlist).where(
                EmployerCandidateShortlist.vacancy_id == context.vacancy.id,
                EmployerCandidateShortlist.candidate_id == candidate_id,
            )
        ).scalar_one()
        assert entry.stage == "offer"
        assert entry.updated_at != controlled_updated_at
    finally:
        session.close()


def test_repeated_put_after_patch_does_not_reset_stage(
    shortlist_client: tuple[TestClient, ShortlistContext],
) -> None:
    client, context = shortlist_client
    candidate_id = context.candidate_ids[0]
    created = _put(client, context.vacancy.id, candidate_id).json()
    patched = _patch(client, context.vacancy.id, candidate_id, "interview").json()
    repeated = _put(client, context.vacancy.id, candidate_id)

    assert repeated.status_code == 200
    assert repeated.json()["id"] == created["id"] == patched["id"]
    assert repeated.json()["stage"] == "interview"
    assert _get(client, context.vacancy.id).json()["entries"][0]["stage"] == "interview"


def test_patch_rejects_invalid_stage_and_extra_fields(
    shortlist_client: tuple[TestClient, ShortlistContext],
) -> None:
    client, context = shortlist_client
    candidate_id = context.candidate_ids[0]
    assert _put(client, context.vacancy.id, candidate_id).status_code == 200

    invalid = _patch(client, context.vacancy.id, candidate_id, "archived")
    extra = _patch(
        client,
        context.vacancy.id,
        candidate_id,
        "interview",
        employer_id=str(context.employer.id),
    )
    with_note = _patch(
        client,
        context.vacancy.id,
        candidate_id,
        "interview",
        note="should not be accepted here",
    )

    assert invalid.status_code == 422
    assert extra.status_code == 422
    assert with_note.status_code == 422
    assert _get(client, context.vacancy.id).json()["entries"][0]["stage"] == "shortlisted"


def test_patch_missing_entry_returns_shortlist_entry_not_found(
    shortlist_client: tuple[TestClient, ShortlistContext],
) -> None:
    client, context = shortlist_client

    missing = _patch(client, context.vacancy.id, uuid4(), "interview")
    employer_uuid = _patch(
        client, context.vacancy.id, context.employer_user.id, "interview"
    )

    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "SHORTLIST_ENTRY_NOT_FOUND"
    assert employer_uuid.status_code == 404
    assert employer_uuid.json()["error"]["code"] == "SHORTLIST_ENTRY_NOT_FOUND"
    assert _get(client, context.vacancy.id).json() == {"entries": []}


def test_get_returns_entries_across_all_stages_without_reordering_on_patch(
    shortlist_client: tuple[TestClient, ShortlistContext],
) -> None:
    client, context = shortlist_client
    first_candidate, second_candidate, _ = context.candidate_ids
    timestamp = datetime(2026, 7, 25, tzinfo=UTC)
    older_id = UUID(int=10)
    newer_id = UUID(int=20)

    session = context.new_session()
    try:
        session.add_all(
            [
                EmployerCandidateShortlist(
                    id=older_id,
                    employer_id=context.employer.id,
                    vacancy_id=context.vacancy.id,
                    candidate_id=first_candidate,
                    stage="screening",
                    created_at=timestamp,
                    updated_at=timestamp,
                ),
                EmployerCandidateShortlist(
                    id=newer_id,
                    employer_id=context.employer.id,
                    vacancy_id=context.vacancy.id,
                    candidate_id=second_candidate,
                    stage="hired",
                    created_at=timestamp,
                    updated_at=timestamp,
                ),
            ]
        )
        session.commit()
    finally:
        session.close()

    before = _get(client, context.vacancy.id)
    assert [entry["id"] for entry in before.json()["entries"]] == [
        str(newer_id),
        str(older_id),
    ]
    assert {entry["stage"] for entry in before.json()["entries"]} == {
        "screening",
        "hired",
    }

    patched = _patch(client, context.vacancy.id, first_candidate, "interview")
    assert patched.status_code == 200

    after = _get(client, context.vacancy.id)
    assert [entry["id"] for entry in after.json()["entries"]] == [
        str(newer_id),
        str(older_id),
    ]
    assert after.json()["entries"][1]["stage"] == "interview"


def test_stage_update_is_isolated_across_vacancies(
    shortlist_client: tuple[TestClient, ShortlistContext],
) -> None:
    client, context = shortlist_client
    candidate_id = context.candidate_ids[0]
    first = _put(client, context.vacancy.id, candidate_id).json()
    second = _put(client, context.second_vacancy.id, candidate_id).json()

    patched = _patch(client, context.vacancy.id, candidate_id, "offer")
    assert patched.status_code == 200
    assert patched.json()["stage"] == "offer"
    assert patched.json()["id"] == first["id"]

    other = _get(client, context.second_vacancy.id).json()["entries"][0]
    assert other["id"] == second["id"]
    assert other["stage"] == "shortlisted"


def test_delete_after_non_default_stage_remains_idempotent(
    shortlist_client: tuple[TestClient, ShortlistContext],
) -> None:
    client, context = shortlist_client
    candidate_id = context.candidate_ids[0]
    assert _put(client, context.vacancy.id, candidate_id).status_code == 200
    assert _patch(client, context.vacancy.id, candidate_id, "interview").status_code == 200

    first_delete = _delete(client, context.vacancy.id, candidate_id)
    repeated_delete = _delete(client, context.vacancy.id, candidate_id)

    assert first_delete.status_code == 204
    assert first_delete.content == b""
    assert repeated_delete.status_code == 204
    assert repeated_delete.content == b""
    assert _get(client, context.vacancy.id).json() == {"entries": []}


def test_note_model_column_is_nullable_text() -> None:
    from sqlalchemy import Text

    from app.db.base import Base
    import app.models  # noqa: F401

    column = Base.metadata.tables["employer_candidate_shortlists"].c.note
    assert isinstance(column.type, Text)
    assert column.nullable is True
    assert column.server_default is None


def test_note_migration_contract_and_single_head() -> None:
    from pathlib import Path

    from alembic.config import Config
    from alembic.script import ScriptDirectory

    migration_path = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "20260726_0018_employer_shortlist_note.py"
    )
    source = migration_path.read_text(encoding="utf-8")
    assert 'revision: str = "20260726_0018"' in source
    assert 'down_revision: Union[str, None] = "20260726_0017"' in source
    assert 'sa.Column("note", sa.Text(), nullable=True)' in source
    assert 'op.drop_column("employer_candidate_shortlists", "note")' in source

    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    script = ScriptDirectory.from_config(config)
    heads = script.get_heads()
    assert heads == ["20260726_0020"]
    assert 'down_revision: Union[str, None] = "20260726_0018"' in (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "20260726_0019_employer_interview_scorecards.py"
    ).read_text(encoding="utf-8")
    assert 'down_revision: Union[str, None] = "20260726_0019"' in (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "20260726_0020_career_companion.py"
    ).read_text(encoding="utf-8")


def test_note_patch_create_update_and_get(
    shortlist_client: tuple[TestClient, ShortlistContext],
) -> None:
    client, context = shortlist_client
    candidate_id = context.candidate_ids[0]
    assert _put(client, context.vacancy.id, candidate_id).json()["note"] is None

    created = _patch_note(
        client, context.vacancy.id, candidate_id, {"note": "Strong backend experience"}
    )
    assert created.status_code == 200
    assert created.json()["note"] == "Strong backend experience"
    assert set(created.json()) == SHORTLIST_RESPONSE_KEYS
    assert "employer_id" not in created.json()

    updated = _patch_note(
        client, context.vacancy.id, candidate_id, {"note": "Updated hiring note"}
    )
    assert updated.status_code == 200
    assert updated.json()["note"] == "Updated hiring note"
    assert _get(client, context.vacancy.id).json()["entries"][0]["note"] == (
        "Updated hiring note"
    )


def test_note_normalization_contract(
    shortlist_client: tuple[TestClient, ShortlistContext],
) -> None:
    client, context = shortlist_client
    candidate_id = context.candidate_ids[0]
    assert _put(client, context.vacancy.id, candidate_id).status_code == 200

    stripped = _patch_note(
        client, context.vacancy.id, candidate_id, {"note": "  outer trim  "}
    )
    assert stripped.status_code == 200
    assert stripped.json()["note"] == "outer trim"

    multiline = _patch_note(
        client,
        context.vacancy.id,
        candidate_id,
        {"note": " line one\n  indented two \n"},
    )
    assert multiline.status_code == 200
    assert multiline.json()["note"] == "line one\n  indented two"

    for clear_body in ({"note": None}, {"note": ""}, {"note": "   "}, {"note": "\n\t "}):
        cleared = _patch_note(client, context.vacancy.id, candidate_id, clear_body)
        assert cleared.status_code == 200
        assert cleared.json()["note"] is None

    assert _patch_note(client, context.vacancy.id, candidate_id, {}).status_code == 422
    assert (
        _patch_note(
            client,
            context.vacancy.id,
            candidate_id,
            {"note": "ok", "extra": "nope"},
        ).status_code
        == 422
    )
    assert (
        _patch_note(
            client,
            context.vacancy.id,
            candidate_id,
            {"note": None, "stage": "interview"},
        ).status_code
        == 422
    )

    spaces_only = _patch_note(
        client, context.vacancy.id, candidate_id, {"note": " " * 10000}
    )
    assert spaces_only.status_code == 200
    assert spaces_only.json()["note"] is None

    accepted = _patch_note(
        client, context.vacancy.id, candidate_id, {"note": "a" * 5000}
    )
    assert accepted.status_code == 200
    assert accepted.json()["note"] == "a" * 5000

    padded_accepted = _patch_note(
        client,
        context.vacancy.id,
        candidate_id,
        {"note": " " + ("a" * 5000) + " "},
    )
    assert padded_accepted.status_code == 200
    assert padded_accepted.json()["note"] == "a" * 5000
    assert len(padded_accepted.json()["note"]) == 5000

    rejected = _patch_note(
        client, context.vacancy.id, candidate_id, {"note": "a" * 5001}
    )
    assert rejected.status_code == 422
    assert rejected.json()["error"]["code"] == "VALIDATION_ERROR"

    padded_rejected = _patch_note(
        client,
        context.vacancy.id,
        candidate_id,
        {"note": " " + ("a" * 5001) + " "},
    )
    assert padded_rejected.status_code == 422
    assert padded_rejected.json()["error"]["code"] == "VALIDATION_ERROR"

    internal = _patch_note(
        client, context.vacancy.id, candidate_id, {"note": "\ta  b\n\nc\t"}
    )
    assert internal.status_code == 200
    assert internal.json()["note"] == "a  b\n\nc"


def test_same_note_patch_is_true_noop(
    shortlist_client: tuple[TestClient, ShortlistContext],
) -> None:
    client, context = shortlist_client
    candidate_id = context.candidate_ids[0]
    assert _put(client, context.vacancy.id, candidate_id).status_code == 200

    first = _patch_note(
        client, context.vacancy.id, candidate_id, {"note": "Keep this note"}
    ).json()
    controlled = datetime(2026, 2, 1, tzinfo=UTC)

    session = context.new_session()
    try:
        session.execute(
            update(EmployerCandidateShortlist)
            .where(
                EmployerCandidateShortlist.vacancy_id == context.vacancy.id,
                EmployerCandidateShortlist.candidate_id == candidate_id,
            )
            .values(updated_at=controlled)
        )
        session.commit()
    finally:
        session.close()

    same = _patch_note(
        client, context.vacancy.id, candidate_id, {"note": "Keep this note"}
    )
    equivalent = _patch_note(
        client, context.vacancy.id, candidate_id, {"note": "  Keep this note  "}
    )
    assert same.status_code == 200
    assert same.json()["note"] == "Keep this note"
    assert equivalent.status_code == 200
    assert equivalent.json()["note"] == "Keep this note"
    assert first["created_at"] == same.json()["created_at"]

    session = context.new_session()
    try:
        entry = session.execute(
            select(EmployerCandidateShortlist).where(
                EmployerCandidateShortlist.vacancy_id == context.vacancy.id,
                EmployerCandidateShortlist.candidate_id == candidate_id,
            )
        ).scalar_one()
        assert entry.note == "Keep this note"
        assert entry.updated_at == controlled
    finally:
        session.close()

    same_null_seed = _patch_note(
        client, context.vacancy.id, candidate_id, {"note": None}
    )
    assert same_null_seed.status_code == 200
    assert same_null_seed.json()["note"] is None

    session = context.new_session()
    try:
        session.execute(
            update(EmployerCandidateShortlist)
            .where(
                EmployerCandidateShortlist.vacancy_id == context.vacancy.id,
                EmployerCandidateShortlist.candidate_id == candidate_id,
            )
            .values(updated_at=controlled)
        )
        session.commit()
    finally:
        session.close()

    same_null = _patch_note(
        client, context.vacancy.id, candidate_id, {"note": None}
    )
    whitespace_null = _patch_note(
        client, context.vacancy.id, candidate_id, {"note": "  \n"}
    )

    assert same_null.status_code == 200
    assert same_null.json()["note"] is None
    assert whitespace_null.status_code == 200
    assert whitespace_null.json()["note"] is None

    session = context.new_session()
    try:
        entry = session.execute(
            select(EmployerCandidateShortlist).where(
                EmployerCandidateShortlist.vacancy_id == context.vacancy.id,
                EmployerCandidateShortlist.candidate_id == candidate_id,
            )
        ).scalar_one()
        assert entry.note is None
        assert entry.updated_at == controlled
    finally:
        session.close()

    session = context.new_session()
    try:
        session.execute(
            update(EmployerCandidateShortlist)
            .where(
                EmployerCandidateShortlist.vacancy_id == context.vacancy.id,
                EmployerCandidateShortlist.candidate_id == candidate_id,
            )
            .values(note="Keep this note", updated_at=controlled)
        )
        session.commit()
    finally:
        session.close()

    same_text_again = _patch_note(
        client, context.vacancy.id, candidate_id, {"note": "Keep this note"}
    )
    assert same_text_again.status_code == 200
    session = context.new_session()
    try:
        entry = session.execute(
            select(EmployerCandidateShortlist).where(
                EmployerCandidateShortlist.vacancy_id == context.vacancy.id,
                EmployerCandidateShortlist.candidate_id == candidate_id,
            )
        ).scalar_one()
        assert entry.note == "Keep this note"
        assert entry.updated_at == controlled
    finally:
        session.close()


def test_real_note_change_updates_updated_at(
    shortlist_client: tuple[TestClient, ShortlistContext],
) -> None:
    client, context = shortlist_client
    candidate_id = context.candidate_ids[0]
    created = _put(client, context.vacancy.id, candidate_id).json()
    controlled = datetime(2026, 3, 1, tzinfo=UTC)

    def _force_updated_at() -> None:
        session = context.new_session()
        try:
            session.execute(
                update(EmployerCandidateShortlist)
                .where(
                    EmployerCandidateShortlist.vacancy_id == context.vacancy.id,
                    EmployerCandidateShortlist.candidate_id == candidate_id,
                )
                .values(updated_at=controlled)
            )
            session.commit()
        finally:
            session.close()

    def _read_entry() -> tuple[str | None, datetime]:
        session = context.new_session()
        try:
            entry = session.execute(
                select(EmployerCandidateShortlist).where(
                    EmployerCandidateShortlist.vacancy_id == context.vacancy.id,
                    EmployerCandidateShortlist.candidate_id == candidate_id,
                )
            ).scalar_one()
            return entry.note, entry.updated_at
        finally:
            session.close()

    _force_updated_at()
    changed = _patch_note(
        client, context.vacancy.id, candidate_id, {"note": "Now changed"}
    )
    assert changed.status_code == 200
    assert changed.json()["note"] == "Now changed"
    assert changed.json()["created_at"] == created["created_at"]
    assert changed.json()["updated_at"] != controlled.isoformat().replace("+00:00", "Z")
    assert changed.json()["updated_at"] != "2026-03-01T00:00:00+00:00"
    assert changed.json()["updated_at"] != "2026-03-01T00:00:00Z"
    note_value, updated_at = _read_entry()
    assert note_value == "Now changed"
    assert updated_at != controlled

    _force_updated_at()
    rewritten = _patch_note(
        client, context.vacancy.id, candidate_id, {"note": "Different text"}
    )
    assert rewritten.status_code == 200
    assert rewritten.json()["note"] == "Different text"
    assert rewritten.json()["updated_at"] != controlled.isoformat().replace("+00:00", "Z")
    assert rewritten.json()["updated_at"] != "2026-03-01T00:00:00+00:00"
    assert rewritten.json()["updated_at"] != "2026-03-01T00:00:00Z"
    note_value, updated_at = _read_entry()
    assert note_value == "Different text"
    assert updated_at != controlled

    _force_updated_at()
    cleared = _patch_note(client, context.vacancy.id, candidate_id, {"note": None})
    assert cleared.status_code == 200
    assert cleared.json()["note"] is None
    assert cleared.json()["updated_at"] != controlled.isoformat().replace("+00:00", "Z")
    assert cleared.json()["updated_at"] != "2026-03-01T00:00:00+00:00"
    assert cleared.json()["updated_at"] != "2026-03-01T00:00:00Z"
    note_value, updated_at = _read_entry()
    assert note_value is None
    assert updated_at != controlled


def test_repeated_put_after_note_update_does_not_reset_note(
    shortlist_client: tuple[TestClient, ShortlistContext],
) -> None:
    client, context = shortlist_client
    candidate_id = context.candidate_ids[0]
    assert _put(client, context.vacancy.id, candidate_id).status_code == 200
    patched = _patch_note(
        client, context.vacancy.id, candidate_id, {"note": "Persisted note"}
    ).json()
    repeated = _put(client, context.vacancy.id, candidate_id)

    assert repeated.status_code == 200
    assert repeated.json()["id"] == patched["id"]
    assert repeated.json()["note"] == "Persisted note"
    assert _get(client, context.vacancy.id).json()["entries"][0]["note"] == (
        "Persisted note"
    )


def test_stage_update_preserves_note(
    shortlist_client: tuple[TestClient, ShortlistContext],
) -> None:
    client, context = shortlist_client
    candidate_id = context.candidate_ids[0]
    assert _put(client, context.vacancy.id, candidate_id).status_code == 200
    assert (
        _patch_note(
            client, context.vacancy.id, candidate_id, {"note": "Stage safe note"}
        ).status_code
        == 200
    )

    changed = _patch(client, context.vacancy.id, candidate_id, "interview")
    assert changed.status_code == 200
    assert changed.json()["stage"] == "interview"
    assert changed.json()["note"] == "Stage safe note"
    assert "note" in changed.json()

    same_stage = _patch(client, context.vacancy.id, candidate_id, "interview")
    assert same_stage.status_code == 200
    assert same_stage.json()["note"] == "Stage safe note"
    assert _get(client, context.vacancy.id).json()["entries"][0]["note"] == (
        "Stage safe note"
    )


def test_listing_returns_notes_without_reordering_on_note_edit(
    shortlist_client: tuple[TestClient, ShortlistContext],
) -> None:
    client, context = shortlist_client
    first_candidate, second_candidate, _ = context.candidate_ids
    timestamp = datetime(2026, 7, 25, tzinfo=UTC)
    older_id = UUID(int=30)
    newer_id = UUID(int=40)

    session = context.new_session()
    try:
        session.add_all(
            [
                EmployerCandidateShortlist(
                    id=older_id,
                    employer_id=context.employer.id,
                    vacancy_id=context.vacancy.id,
                    candidate_id=first_candidate,
                    stage="screening",
                    note="Older note",
                    created_at=timestamp,
                    updated_at=timestamp,
                ),
                EmployerCandidateShortlist(
                    id=newer_id,
                    employer_id=context.employer.id,
                    vacancy_id=context.vacancy.id,
                    candidate_id=second_candidate,
                    stage="hired",
                    note="Newer note",
                    created_at=timestamp,
                    updated_at=timestamp,
                ),
            ]
        )
        session.commit()
    finally:
        session.close()

    before = _get(client, context.vacancy.id)
    assert [entry["id"] for entry in before.json()["entries"]] == [
        str(newer_id),
        str(older_id),
    ]
    assert [entry["note"] for entry in before.json()["entries"]] == [
        "Newer note",
        "Older note",
    ]
    assert {entry["stage"] for entry in before.json()["entries"]} == {
        "screening",
        "hired",
    }

    patched = _patch_note(
        client, context.vacancy.id, first_candidate, {"note": "Edited older"}
    )
    assert patched.status_code == 200

    after = _get(client, context.vacancy.id)
    assert [entry["id"] for entry in after.json()["entries"]] == [
        str(newer_id),
        str(older_id),
    ]
    assert after.json()["entries"][1]["note"] == "Edited older"


def test_note_privacy_and_vacancy_isolation(
    shortlist_client: tuple[TestClient, ShortlistContext],
) -> None:
    client, context = shortlist_client
    candidate_id = context.candidate_ids[0]
    missing_candidate_id = uuid4()
    assert _put(client, context.vacancy.id, candidate_id).status_code == 200
    assert (
        _patch_note(
            client, context.vacancy.id, candidate_id, {"note": "Owned note"}
        ).status_code
        == 200
    )
    assert _put(client, context.second_vacancy.id, candidate_id).status_code == 200
    assert (
        _patch_note(
            client,
            context.second_vacancy.id,
            candidate_id,
            {"note": "Second vacancy note"},
        ).status_code
        == 200
    )

    missing = _patch_note(
        client, context.vacancy.id, missing_candidate_id, {"note": "Nope"}
    )
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "SHORTLIST_ENTRY_NOT_FOUND"

    foreign_known = _patch_note(
        client, context.foreign_vacancy.id, candidate_id, {"note": "Leak"}
    )
    foreign_missing = _patch_note(
        client, context.foreign_vacancy.id, missing_candidate_id, {"note": "Leak"}
    )
    foreign_get = _get(client, context.foreign_vacancy.id)
    for response in (foreign_known, foreign_missing, foreign_get):
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "VACANCY_NOT_FOUND"

    session = context.new_session()
    try:
        foreign_entry = session.get(EmployerCandidateShortlist, context.foreign_entry_id)
        assert foreign_entry is not None
        assert foreign_entry.note is None
        owned = session.execute(
            select(EmployerCandidateShortlist).where(
                EmployerCandidateShortlist.vacancy_id == context.vacancy.id,
                EmployerCandidateShortlist.candidate_id == candidate_id,
            )
        ).scalar_one()
        second = session.execute(
            select(EmployerCandidateShortlist).where(
                EmployerCandidateShortlist.vacancy_id == context.second_vacancy.id,
                EmployerCandidateShortlist.candidate_id == candidate_id,
            )
        ).scalar_one()
        assert owned.note == "Owned note"
        assert second.note == "Second vacancy note"
    finally:
        session.close()

    assert _get(client, context.vacancy.id).json()["entries"][0]["note"] == "Owned note"
    assert (
        _get(client, context.second_vacancy.id).json()["entries"][0]["note"]
        == "Second vacancy note"
    )


def test_note_route_rejects_candidate_role_and_unauthenticated(
    shortlist_client: tuple[TestClient, ShortlistContext],
) -> None:
    from app.api.errors import api_error

    client, context = shortlist_client
    candidate_id = context.candidate_ids[0]
    assert _put(client, context.vacancy.id, candidate_id).status_code == 200
    path = (
        f"/api/v1/employer/vacancies/{context.vacancy.id}/shortlist/{candidate_id}/note"
    )

    app.dependency_overrides[require_employer] = lambda: (_ for _ in ()).throw(
        api_error(403, "FORBIDDEN", "Employer role required")
    )
    forbidden = client.patch(path, json={"note": "secret"})
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "FORBIDDEN"

    app.dependency_overrides.pop(require_employer, None)
    unauthenticated = client.patch(path, json={"note": "secret"})
    assert unauthenticated.status_code == 401

    app.dependency_overrides[require_employer] = lambda: context.employer_user
    still_owned = _get(client, context.vacancy.id)
    assert still_owned.status_code == 200
    assert still_owned.json()["entries"][0]["note"] is None


def test_delete_with_note_and_reput_starts_null(
    shortlist_client: tuple[TestClient, ShortlistContext],
) -> None:
    client, context = shortlist_client
    candidate_id = context.candidate_ids[0]
    assert _put(client, context.vacancy.id, candidate_id).status_code == 200
    assert (
        _patch_note(
            client, context.vacancy.id, candidate_id, {"note": "Will be deleted"}
        ).status_code
        == 200
    )

    first_delete = _delete(client, context.vacancy.id, candidate_id)
    repeated_delete = _delete(client, context.vacancy.id, candidate_id)
    assert first_delete.status_code == 204
    assert first_delete.content == b""
    assert repeated_delete.status_code == 204
    assert repeated_delete.content == b""
    assert _get(client, context.vacancy.id).json() == {"entries": []}

    restored = _put(client, context.vacancy.id, candidate_id)
    assert restored.status_code == 200
    assert restored.json()["note"] is None
    assert _get(client, context.vacancy.id).json()["entries"][0]["note"] is None


def test_note_database_error_returns_generic_code(
    shortlist_client: tuple[TestClient, ShortlistContext],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from sqlalchemy.orm import Session

    client, context = shortlist_client
    candidate_id = context.candidate_ids[0]
    assert _put(client, context.vacancy.id, candidate_id).status_code == 200

    def boom_commit(self: Session) -> None:
        raise SQLAlchemyError("secret note body must not leak")

    monkeypatch.setattr(Session, "commit", boom_commit)
    response = _patch_note(
        client, context.vacancy.id, candidate_id, {"note": "sensitive hiring note"}
    )
    assert response.status_code == 500
    payload = response.json()
    assert payload["error"]["code"] == "DATABASE_ERROR"
    assert payload["error"]["message"] == "Database operation failed"
    assert "secret note body" not in response.text
    assert "sensitive hiring note" not in response.text

    monkeypatch.undo()
    session = context.new_session()
    try:
        entry = session.execute(
            select(EmployerCandidateShortlist).where(
                EmployerCandidateShortlist.vacancy_id == context.vacancy.id,
                EmployerCandidateShortlist.candidate_id == candidate_id,
            )
        ).scalar_one()
        assert entry.note is None
    finally:
        session.close()

def _add_ineligible_candidate(
    session: Session,
    *,
    display_name: str | None = None,
    status: str = "active",
) -> UUID:
    user = User(
        id=uuid4(),
        email=f"shortlist-ineligible-{uuid4()}@example.com",
        password_hash="hash",
        role="candidate",
        status=status,
    )
    profile = CandidateProfile(
        id=uuid4(),
        user_id=user.id,
        display_name=display_name,
        onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
    )
    session.add_all([user, profile])
    session.flush()
    return profile.id


def test_save_rejects_shell_and_suspended_candidates(
    shortlist_client: tuple[TestClient, ShortlistContext],
) -> None:
    client, context = shortlist_client
    session = context.new_session()
    try:
        shell_id = _add_ineligible_candidate(session, display_name=None)
        blank_id = _add_ineligible_candidate(session, display_name="   ")
        suspended_id = _add_ineligible_candidate(
            session, display_name="Suspended Candidate", status="suspended"
        )
        session.commit()
    finally:
        session.close()

    for candidate_id in (shell_id, blank_id, suspended_id):
        response = _put(client, context.vacancy.id, candidate_id)
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "CANDIDATE_NOT_FOUND"

    assert _get(client, context.vacancy.id).json() == {"entries": []}


def test_save_accepts_valid_named_candidate_with_zero_match_context(
    shortlist_client: tuple[TestClient, ShortlistContext],
) -> None:
    client, context = shortlist_client
    candidate_id = context.candidate_ids[0]
    response = _put(client, context.vacancy.id, candidate_id)
    assert response.status_code == 200
    assert response.json()["candidate_id"] == str(candidate_id)


def test_stale_ineligible_shortlist_rows_are_soft_filtered_and_mutable_selectively(
    shortlist_client: tuple[TestClient, ShortlistContext],
) -> None:
    client, context = shortlist_client
    valid_id = context.candidate_ids[0]
    assert _put(client, context.vacancy.id, valid_id).status_code == 200

    session = context.new_session()
    try:
        shell_id = _add_ineligible_candidate(session, display_name=None)
        suspended_id = _add_ineligible_candidate(
            session, display_name="Was Eligible", status="suspended"
        )
        session.add_all(
            [
                EmployerCandidateShortlist(
                    id=uuid4(),
                    employer_id=context.employer.id,
                    vacancy_id=context.vacancy.id,
                    candidate_id=shell_id,
                ),
                EmployerCandidateShortlist(
                    id=uuid4(),
                    employer_id=context.employer.id,
                    vacancy_id=context.vacancy.id,
                    candidate_id=suspended_id,
                ),
            ]
        )
        session.commit()
    finally:
        session.close()

    listing = _get(client, context.vacancy.id)
    assert listing.status_code == 200
    listed_ids = {entry["candidate_id"] for entry in listing.json()["entries"]}
    assert listed_ids == {str(valid_id)}
    assert str(shell_id) not in listed_ids
    assert str(suspended_id) not in listed_ids

    stage = _patch(client, context.vacancy.id, shell_id, "interview")
    note = _patch_note(client, context.vacancy.id, suspended_id, {"note": "stale"})
    assert stage.status_code == 404
    assert stage.json()["error"]["code"] == "CANDIDATE_NOT_FOUND"
    assert note.status_code == 404
    assert note.json()["error"]["code"] == "CANDIDATE_NOT_FOUND"

    delete_shell = _delete(client, context.vacancy.id, shell_id)
    delete_suspended = _delete(client, context.vacancy.id, suspended_id)
    assert delete_shell.status_code == 204
    assert delete_suspended.status_code == 204

    verify = context.new_session()
    try:
        remaining = list(
            verify.execute(
                select(EmployerCandidateShortlist).where(
                    EmployerCandidateShortlist.vacancy_id == context.vacancy.id
                )
            )
            .scalars()
            .all()
        )
        assert {entry.candidate_id for entry in remaining} == {valid_id}
    finally:
        verify.close()
