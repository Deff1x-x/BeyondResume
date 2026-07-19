"""Background execution of github_scan Jobs on the shared Job engine."""

from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.integrations.github import (
    GitHubProviderError,
    GitHubRepositoryNotFoundError,
    get_github_provider,
)
from app.models.job import Job, JobType
from app.services.candidate import CandidateProfileNotFoundError
from app.services.github_evidence import GitHubRepositorySnapshotNotFoundError
from app.services.github_full_scan import run_github_repository_scan
from app.services.github_scan import (
    GitHubRepositorySourceNotFoundError,
    GitHubSnapshotIdentityMismatchError,
)
from app.services.github_skill_reextraction import reextract_github_evidence_skills
from app.services.github_skill_reextraction_errors import GitHubEvidenceSourceConsistencyError
from app.services.jobs import (
    JobTransitionError,
    claim_job,
    complete_running_job,
    fail_running_job,
    get_or_create_active_subject_job,
    SubjectJobRequestResult,
)
from app.utils.github_evidence import GitHubPersistedSnapshotValidationError
from app.utils.github_snapshot import GitHubSnapshotValidationError

GITHUB_SCAN_SUBJECT_TYPE = "github_repository"


def request_github_scan(
    session: Session, *, candidate_id: UUID, repository_id: UUID
) -> SubjectJobRequestResult:
    """Return the active scan Job for a repository or create a pending one."""
    return get_or_create_active_subject_job(
        session,
        job_type=JobType.GITHUB_SCAN,
        candidate_id=candidate_id,
        subject_type=GITHUB_SCAN_SUBJECT_TYPE,
        subject_id=repository_id,
    )


def _failure_details(error: BaseException) -> tuple[str, str]:
    if isinstance(error, GitHubRepositoryNotFoundError):
        return "GITHUB_REPOSITORY_UNAVAILABLE", "Repository data is not available for analysis"
    if isinstance(error, GitHubProviderError):
        return "GITHUB_PROVIDER_ERROR", "GitHub repository data could not be fetched"
    if isinstance(error, SQLAlchemyError):
        return "DATABASE_ERROR", "Database operation failed"
    return "GITHUB_ANALYSIS_ERROR", "GitHub repository analysis failed"


def run_github_scan_job(session: Session, job_id: UUID) -> Job:
    """Run one pending github_scan Job using the shared Job state machine."""
    job = claim_job(session, job_id)
    if (
        job.job_type != JobType.GITHUB_SCAN
        or job.candidate_id is None
        or job.subject_id is None
    ):
        raise JobTransitionError("Job is not a github scan job")

    try:
        scan_result = run_github_repository_scan(session, job.candidate_id, get_github_provider())
        reextract_github_evidence_skills(
            session,
            candidate_id=job.candidate_id,
            github_repository_id=job.subject_id,
            evidence_unit_id=scan_result.evidence_unit.id,
        )
    except (
        GitHubProviderError,
        CandidateProfileNotFoundError,
        GitHubRepositorySourceNotFoundError,
        GitHubRepositorySnapshotNotFoundError,
        GitHubSnapshotIdentityMismatchError,
        GitHubEvidenceSourceConsistencyError,
        GitHubPersistedSnapshotValidationError,
        GitHubSnapshotValidationError,
        SQLAlchemyError,
    ) as error:
        session.rollback()
        code, message = _failure_details(error)
        return fail_running_job(session, job, code, message)

    return complete_running_job(session, job)


def run_github_scan_job_task(job_id: UUID) -> None:
    """Run a background scan using a session owned by the background task."""
    session = SessionLocal()
    try:
        run_github_scan_job(session, job_id)
    finally:
        session.close()
