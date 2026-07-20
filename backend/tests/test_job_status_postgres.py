from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import engine
from app.models.candidate_profile import CandidateProfile, OnboardingStatus
from app.models.job import Job, JobStatus, JobType
from app.models.user import User
from app.services.jobs import claim_job, complete_running_job, get_or_create_active_subject_job


@pytest.fixture
def postgres_session() -> Session:
    """Run integration assertions in an outer transaction that is always rolled back."""
    try:
        connection = engine.connect()
    except SQLAlchemyError as error:
        pytest.skip(f"PostgreSQL is unavailable: {error}")

    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


def test_job_status_uses_lowercase_postgres_enum_values(postgres_session: Session) -> None:
    user = User(
        id=uuid4(),
        email=f"job-status-{uuid4()}@example.com",
        password_hash="hash",
        role="candidate",
        status="active",
    )
    profile = CandidateProfile(
        id=uuid4(),
        user_id=user.id,
        onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
    )
    postgres_session.add_all([user, profile])
    postgres_session.flush()

    job = Job(id=uuid4(), job_type=JobType.PROFILE_ANALYSIS, status=JobStatus.PENDING)
    postgres_session.add(job)
    postgres_session.flush()

    assert postgres_session.scalar(select(Job).where(Job.status == JobStatus.PENDING)) is job
    assert postgres_session.scalar(
        select(Job).where(Job.status.in_([JobStatus.PENDING, JobStatus.RUNNING]))
    ) is job

    job.status = JobStatus.RUNNING
    postgres_session.flush()
    job.status = JobStatus.COMPLETED
    postgres_session.flush()
    postgres_session.expire_all()
    hydrated = postgres_session.get(Job, job.id)
    assert hydrated is not None
    assert hydrated.status is JobStatus.COMPLETED

    result = get_or_create_active_subject_job(
        postgres_session,
        job_type=JobType.GITHUB_SCAN,
        candidate_id=profile.id,
        subject_type="github_repository",
        subject_id=uuid4(),
    )
    assert result.created is True
    assert result.job.status is JobStatus.PENDING

    claimed = claim_job(postgres_session, result.job.id)
    assert claimed.status is JobStatus.RUNNING
    completed = complete_running_job(postgres_session, claimed)
    assert completed.status is JobStatus.COMPLETED
