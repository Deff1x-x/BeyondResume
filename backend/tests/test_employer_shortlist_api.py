from collections.abc import Callable, Generator
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
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


def _delete(client: TestClient, vacancy_id: UUID, candidate_id: UUID):
    return client.delete(
        f"/api/v1/employer/vacancies/{vacancy_id}/shortlist/{candidate_id}"
    )


def _get(client: TestClient, vacancy_id: UUID):
    return client.get(f"/api/v1/employer/vacancies/{vacancy_id}/shortlist")


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
    assert "employer_id" not in first.json()
    assert set(first.json()) == {
        "id",
        "vacancy_id",
        "candidate_id",
        "created_at",
        "updated_at",
    }
    assert first.json()["vacancy_id"] == str(context.vacancy.id)
    assert first.json()["candidate_id"] == str(candidate_id)
    assert persisted.status_code == 200
    assert persisted.json()["entries"] == [first.json()]
    assert all("employer_id" not in entry for entry in persisted.json()["entries"])


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

    for response in (save_known, save_missing, listing, removal):
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "VACANCY_NOT_FOUND"

    session = context.new_session()
    try:
        assert session.get(EmployerCandidateShortlist, context.foreign_entry_id) is not None
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
