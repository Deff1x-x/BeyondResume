"""Service and model behavior for Interview Scorecard."""

from collections.abc import Callable, Generator
from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import engine
from app.models.application import Application
from app.models.candidate_profile import CandidateProfile, OnboardingStatus
from app.models.employer_candidate_shortlist import EmployerCandidateShortlist
from app.models.employer_interview_scorecard import EmployerInterviewScorecard
from app.models.employer_profile import EmployerProfile
from app.models.user import User
from app.models.vacancy import Vacancy
from app.services.employer_shortlist import (
    remove_candidate_from_shortlist,
    save_candidate_to_shortlist,
)
from app.services.interview_scorecard import (
    ScorecardCandidateNotFoundError,
    ScorecardNotFoundError,
    ScorecardValidationError,
    build_scorecard_summary,
    get_interview_scorecard,
    upsert_interview_scorecard,
)


@dataclass(frozen=True)
class ScorecardServiceContext:
    employer: EmployerProfile
    vacancy: Vacancy
    second_vacancy: Vacancy
    candidate_ids: tuple[UUID, UUID]
    new_session: Callable[[], Session]


@pytest.fixture
def scorecard_service_ctx() -> Generator[ScorecardServiceContext, None, None]:
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
        email=f"scorecard-svc-{uuid4()}@example.com",
        password_hash="hash",
        role="employer",
        status="active",
    )
    employer = EmployerProfile(id=uuid4(), user_id=employer_user.id, company_name="Scorecard Co")
    vacancy = Vacancy(id=uuid4(), employer_id=employer.id, title="Backend", status="open")
    second_vacancy = Vacancy(id=uuid4(), employer_id=employer.id, title="Platform", status="open")
    candidate_users = [
        User(
            id=uuid4(),
            email=f"scorecard-cand-{uuid4()}@example.com",
            password_hash="hash",
            role="candidate",
            status="active",
        )
        for _ in range(2)
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
    applications = [
        Application(
            id=uuid4(),
            vacancy_id=owned_vacancy.id,
            candidate_id=candidate.id,
            status="applied",
        )
        for owned_vacancy in (vacancy, second_vacancy)
        for candidate in candidates
    ]
    setup.add_all(
        [
            employer_user,
            *candidate_users,
            employer,
            vacancy,
            second_vacancy,
            *candidates,
            *applications,
        ]
    )
    setup.commit()
    setup.close()

    def new_session() -> Session:
        return Session(bind=connection, join_transaction_mode="create_savepoint")

    try:
        yield ScorecardServiceContext(
            employer=employer,
            vacancy=vacancy,
            second_vacancy=second_vacancy,
            candidate_ids=(candidates[0].id, candidates[1].id),
            new_session=new_session,
        )
    finally:
        transaction.rollback()
        connection.close()


def _upsert(
    session: Session,
    vacancy: Vacancy,
    candidate_id: UUID,
    **overrides: object,
) -> EmployerInterviewScorecard:
    payload: dict[str, object] = {
        "status": "completed",
        "technical_competency": 4,
        "experience_relevance": 3,
        "communication": 5,
        "ownership": 4,
        "interview_summary": "Good interview",
        "interview_notes": "Notes",
        "recommendation": "yes",
    }
    payload.update(overrides)

    def _opt_int(value: object) -> int | None:
        return None if value is None else int(value)  # type: ignore[arg-type]

    return upsert_interview_scorecard(
        session,
        vacancy=vacancy,
        candidate_id=candidate_id,
        status=str(payload["status"]),
        technical_competency=_opt_int(payload["technical_competency"]),
        experience_relevance=_opt_int(payload["experience_relevance"]),
        communication=_opt_int(payload["communication"]),
        ownership=_opt_int(payload["ownership"]),
        interview_summary=payload["interview_summary"],  # type: ignore[arg-type]
        interview_notes=payload["interview_notes"],  # type: ignore[arg-type]
        recommendation=(
            None if payload["recommendation"] is None else str(payload["recommendation"])
        ),
    )


def test_create_scorecard(scorecard_service_ctx: ScorecardServiceContext) -> None:
    session = scorecard_service_ctx.new_session()
    try:
        entry = _upsert(
            session,
            scorecard_service_ctx.vacancy,
            scorecard_service_ctx.candidate_ids[0],
        )
        assert entry.id is not None
        assert entry.recommendation == "yes"
        assert entry.employer_id == scorecard_service_ctx.employer.id
    finally:
        session.close()


def test_repeated_put_updates_same_row(
    scorecard_service_ctx: ScorecardServiceContext,
) -> None:
    session = scorecard_service_ctx.new_session()
    try:
        first = _upsert(
            session,
            scorecard_service_ctx.vacancy,
            scorecard_service_ctx.candidate_ids[0],
        )
        original_id = first.id
        created_at = first.created_at
        second = _upsert(
            session,
            scorecard_service_ctx.vacancy,
            scorecard_service_ctx.candidate_ids[0],
            technical_competency=2,
            recommendation="no",
            interview_summary=None,
            interview_notes=None,
        )
        assert second.id == original_id
        assert second.created_at == created_at
        assert second.technical_competency == 2
        assert second.recommendation == "no"
        assert second.interview_summary is None
        assert second.interview_notes is None
        assert second.updated_at >= created_at
    finally:
        session.close()


def test_unique_vacancy_candidate_enforced(
    scorecard_service_ctx: ScorecardServiceContext,
) -> None:
    session = scorecard_service_ctx.new_session()
    try:
        _upsert(
            session,
            scorecard_service_ctx.vacancy,
            scorecard_service_ctx.candidate_ids[0],
        )
        duplicate = EmployerInterviewScorecard(
            id=uuid4(),
            employer_id=scorecard_service_ctx.employer.id,
            vacancy_id=scorecard_service_ctx.vacancy.id,
            candidate_id=scorecard_service_ctx.candidate_ids[0],
            technical_competency=1,
            experience_relevance=1,
            communication=1,
            ownership=1,
            recommendation="mixed",
        )
        session.add(duplicate)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    finally:
        session.close()


def test_different_vacancy_and_candidate_allowed(
    scorecard_service_ctx: ScorecardServiceContext,
) -> None:
    session = scorecard_service_ctx.new_session()
    try:
        first = _upsert(
            session,
            scorecard_service_ctx.vacancy,
            scorecard_service_ctx.candidate_ids[0],
        )
        other_vacancy = _upsert(
            session,
            scorecard_service_ctx.second_vacancy,
            scorecard_service_ctx.candidate_ids[0],
            recommendation="mixed",
        )
        other_candidate = _upsert(
            session,
            scorecard_service_ctx.vacancy,
            scorecard_service_ctx.candidate_ids[1],
            recommendation="strong_yes",
        )
        assert first.id != other_vacancy.id
        assert first.id != other_candidate.id
    finally:
        session.close()


def test_no_shortlist_required_and_shortlist_unchanged(
    scorecard_service_ctx: ScorecardServiceContext,
) -> None:
    session = scorecard_service_ctx.new_session()
    try:
        entry = _upsert(
            session,
            scorecard_service_ctx.vacancy,
            scorecard_service_ctx.candidate_ids[0],
        )
        shortlist_entry = session.execute(
            select(EmployerCandidateShortlist).where(
                EmployerCandidateShortlist.vacancy_id == scorecard_service_ctx.vacancy.id,
                EmployerCandidateShortlist.candidate_id == scorecard_service_ctx.candidate_ids[0],
            )
        ).scalar_one_or_none()
        assert shortlist_entry is None

        shortlist = save_candidate_to_shortlist(
            session,
            vacancy=scorecard_service_ctx.vacancy,
            candidate_id=scorecard_service_ctx.candidate_ids[0],
        )
        shortlist.stage = "interview"
        shortlist.note = "Keep this note"
        session.commit()
        session.refresh(shortlist)

        _upsert(
            session,
            scorecard_service_ctx.vacancy,
            scorecard_service_ctx.candidate_ids[0],
            recommendation="no",
        )
        session.refresh(shortlist)
        assert shortlist.stage == "interview"
        assert shortlist.note == "Keep this note"

        remove_candidate_from_shortlist(
            session,
            vacancy=scorecard_service_ctx.vacancy,
            candidate_id=scorecard_service_ctx.candidate_ids[0],
        )
        remaining = get_interview_scorecard(
            session,
            vacancy=scorecard_service_ctx.vacancy,
            candidate_id=scorecard_service_ctx.candidate_ids[0],
        )
        assert remaining.id == entry.id
    finally:
        session.close()


def test_get_missing_raises(scorecard_service_ctx: ScorecardServiceContext) -> None:
    session = scorecard_service_ctx.new_session()
    try:
        with pytest.raises(ScorecardNotFoundError):
            get_interview_scorecard(
                session,
                vacancy=scorecard_service_ctx.vacancy,
                candidate_id=scorecard_service_ctx.candidate_ids[0],
            )
        with pytest.raises(ScorecardCandidateNotFoundError):
            get_interview_scorecard(
                session,
                vacancy=scorecard_service_ctx.vacancy,
                candidate_id=uuid4(),
            )
        with pytest.raises(ScorecardCandidateNotFoundError):
            upsert_interview_scorecard(
                session,
                vacancy=scorecard_service_ctx.vacancy,
                candidate_id=uuid4(),
                status="completed",
                technical_competency=3,
                experience_relevance=3,
                communication=3,
                ownership=3,
                interview_summary=None,
                interview_notes=None,
                recommendation="yes",
            )
    finally:
        session.close()


def test_create_draft_scorecard_allows_null_ratings(
    scorecard_service_ctx: ScorecardServiceContext,
) -> None:
    session = scorecard_service_ctx.new_session()
    try:
        entry = _upsert(
            session,
            scorecard_service_ctx.vacancy,
            scorecard_service_ctx.candidate_ids[0],
            status="draft",
            technical_competency=4,
            experience_relevance=None,
            communication=None,
            ownership=None,
            interview_summary=None,
            interview_notes=None,
            recommendation=None,
        )
        assert entry.status == "draft"
        assert entry.technical_competency == 4
        assert entry.experience_relevance is None
        assert entry.communication is None
        assert entry.ownership is None
        assert entry.recommendation is None
    finally:
        session.close()


def test_completed_scorecard_requires_all_ratings(
    scorecard_service_ctx: ScorecardServiceContext,
) -> None:
    session = scorecard_service_ctx.new_session()
    try:
        with pytest.raises(ScorecardValidationError):
            _upsert(
                session,
                scorecard_service_ctx.vacancy,
                scorecard_service_ctx.candidate_ids[0],
                status="completed",
                communication=None,
            )
        with pytest.raises(ScorecardValidationError):
            _upsert(
                session,
                scorecard_service_ctx.vacancy,
                scorecard_service_ctx.candidate_ids[0],
                status="completed",
                recommendation=None,
            )
    finally:
        session.close()


def test_draft_then_complete_updates_same_row(
    scorecard_service_ctx: ScorecardServiceContext,
) -> None:
    session = scorecard_service_ctx.new_session()
    try:
        draft = _upsert(
            session,
            scorecard_service_ctx.vacancy,
            scorecard_service_ctx.candidate_ids[0],
            status="draft",
            experience_relevance=None,
            communication=None,
            ownership=None,
            recommendation=None,
            interview_summary=None,
            interview_notes=None,
        )
        draft_id = draft.id
        completed = _upsert(
            session,
            scorecard_service_ctx.vacancy,
            scorecard_service_ctx.candidate_ids[0],
            status="completed",
        )
        assert completed.id == draft_id
        assert completed.status == "completed"
        assert completed.recommendation == "yes"
    finally:
        session.close()


def test_build_scorecard_summary_completed(
    scorecard_service_ctx: ScorecardServiceContext,
) -> None:
    session = scorecard_service_ctx.new_session()
    try:
        entry = _upsert(
            session,
            scorecard_service_ctx.vacancy,
            scorecard_service_ctx.candidate_ids[0],
            status="completed",
            technical_competency=4,
            experience_relevance=3,
            communication=5,
            ownership=4,
            recommendation="yes",
        )
        summary = build_scorecard_summary(entry)
        assert summary["status"] == "completed"
        assert summary["completed_criteria_count"] == 4
        assert summary["total_criteria_count"] == 4
        assert summary["average_rating"] == 4.0
        assert summary["strongest_dimensions"] == ["Communication"]
        assert summary["weakest_dimensions"] == ["Experience Relevance"]
        assert summary["unanswered_dimensions"] == []
        assert summary["recommendation"] == "yes"
    finally:
        session.close()


def test_build_scorecard_summary_partial_draft(
    scorecard_service_ctx: ScorecardServiceContext,
) -> None:
    session = scorecard_service_ctx.new_session()
    try:
        entry = _upsert(
            session,
            scorecard_service_ctx.vacancy,
            scorecard_service_ctx.candidate_ids[0],
            status="draft",
            technical_competency=2,
            experience_relevance=4,
            communication=None,
            ownership=None,
            recommendation=None,
            interview_summary=None,
            interview_notes=None,
        )
        summary = build_scorecard_summary(entry)
        assert summary["status"] == "draft"
        assert summary["completed_criteria_count"] == 2
        assert summary["total_criteria_count"] == 4
        assert summary["average_rating"] == 3.0
        assert summary["strongest_dimensions"] == ["Experience Relevance"]
        assert summary["weakest_dimensions"] == ["Technical Competency"]
        assert summary["unanswered_dimensions"] == ["Communication", "Ownership"]
        assert summary["recommendation"] is None
    finally:
        session.close()


def test_build_scorecard_summary_empty_draft(
    scorecard_service_ctx: ScorecardServiceContext,
) -> None:
    session = scorecard_service_ctx.new_session()
    try:
        entry = _upsert(
            session,
            scorecard_service_ctx.vacancy,
            scorecard_service_ctx.candidate_ids[0],
            status="draft",
            technical_competency=None,
            experience_relevance=None,
            communication=None,
            ownership=None,
            recommendation=None,
            interview_summary=None,
            interview_notes=None,
        )
        summary = build_scorecard_summary(entry)
        assert summary["completed_criteria_count"] == 0
        assert summary["average_rating"] is None
        assert summary["strongest_dimensions"] == []
        assert summary["weakest_dimensions"] == []
        assert summary["unanswered_dimensions"] == [
            "Technical Competency",
            "Experience Relevance",
            "Communication",
            "Ownership",
        ]
    finally:
        session.close()
