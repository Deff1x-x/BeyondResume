from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.dependencies import require_candidate
from app.api.errors import api_error
from app.db.session import get_db
from app.models.candidate_profile import CandidateProfile
from app.models.evidence_skill_link import EvidenceSkillLink
from app.models.evidence_unit import EvidenceUnit
from app.models.github_repository import GitHubRepository
from app.models.github_repository_snapshot import GitHubRepositorySnapshot
from app.models.job import Job, JobStatus
from app.models.skill import Skill
from app.models.user import User
from app.schemas.github import (
    GitHubRepositoryConnectRequest,
    GitHubRepositoryDetailResponse,
    GitHubRepositoryResponse,
    GitHubRepositorySkillResponse,
    GitHubRepositorySnapshotSummary,
)
from app.schemas.resume import JobPollingResponse
from app.services.candidate import get_candidate_profile
from app.services.github_repository import (
    GitHubRepositoryConflictError,
    connect_github_repository,
    disconnect_github_repository,
)
from app.services.github_scan_jobs import (
    GITHUB_SCAN_SUBJECT_TYPE,
    request_github_scan,
    run_github_scan_job_task,
)
from app.utils.github_evidence import (
    GitHubPersistedSnapshotValidationError,
    validate_persisted_github_repository_payload,
)
from app.utils.github_url import GitHubRepositoryUrlError

router = APIRouter(prefix="/candidate/github", tags=["github"])


def _require_profile(session: Session, current_user: User) -> CandidateProfile:
    profile = get_candidate_profile(session, current_user.id)
    if profile is None:
        raise api_error(
            409,
            "CANDIDATE_PROFILE_REQUIRED",
            "Create a candidate profile before connecting a GitHub repository",
        )
    return profile


def _get_owned_repository(
    session: Session, candidate_id: UUID, repository_id: UUID
) -> GitHubRepository:
    repository = session.execute(
        select(GitHubRepository).where(
            GitHubRepository.id == repository_id,
            GitHubRepository.candidate_id == candidate_id,
        )
    ).scalar_one_or_none()
    if repository is None:
        raise api_error(404, "GITHUB_REPOSITORY_NOT_FOUND", "GitHub repository not found")
    return repository


def _get_snapshot(
    session: Session, repository_id: UUID
) -> GitHubRepositorySnapshot | None:
    return session.execute(
        select(GitHubRepositorySnapshot).where(
            GitHubRepositorySnapshot.repository_id == repository_id
        )
    ).scalar_one_or_none()


def _latest_scan_job(session: Session, repository_id: UUID) -> Job | None:
    return (
        session.execute(
            select(Job)
            .where(
                Job.subject_type == GITHUB_SCAN_SUBJECT_TYPE,
                Job.subject_id == repository_id,
            )
            .order_by(Job.created_at.desc())
            .limit(1)
        )
        .scalars()
        .first()
    )


def _job_response(job: Job) -> JobPollingResponse:
    return JobPollingResponse(
        id=job.id,
        job_type=job.job_type,
        status=job.status,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        failed_at=job.failed_at,
        error_code=job.error_code,
        error_message=job.error_message,
        resume_status=None,
        retry_available=False,
    )


def _repository_response(
    session: Session, repository: GitHubRepository
) -> GitHubRepositoryResponse:
    job = _latest_scan_job(session, repository.id)
    return GitHubRepositoryResponse(
        id=repository.id,
        repository_url=repository.repository_url,
        created_at=repository.created_at,
        job=_job_response(job) if job is not None else None,
    )


def _snapshot_summary(
    snapshot: GitHubRepositorySnapshot,
) -> GitHubRepositorySnapshotSummary:
    try:
        payload = validate_persisted_github_repository_payload(snapshot.payload)
    except GitHubPersistedSnapshotValidationError:
        raise api_error(
            500, "GITHUB_ANALYSIS_ERROR", "Stored GitHub analysis data is invalid"
        ) from None
    return GitHubRepositorySnapshotSummary(
        description=payload.description,
        is_archived=payload.is_archived,
        languages=list(payload.languages),
        file_count=len(payload.tree_paths),
        manifest_count=len(payload.manifest_paths),
    )


def _repository_skills(
    session: Session, candidate_id: UUID, repository_url: str
) -> list[GitHubRepositorySkillResponse]:
    rows = session.execute(
        select(Skill.canonical_name, Skill.category, EvidenceSkillLink.extraction_confidence)
        .join(EvidenceSkillLink, EvidenceSkillLink.skill_id == Skill.id)
        .join(EvidenceUnit, EvidenceUnit.id == EvidenceSkillLink.evidence_unit_id)
        .where(
            EvidenceUnit.candidate_id == candidate_id,
            EvidenceUnit.source_type == "github_repository",
            EvidenceUnit.source_reference == repository_url,
        )
        .order_by(Skill.canonical_name)
    ).all()
    return [
        GitHubRepositorySkillResponse(
            name=name, category=category, extraction_confidence=float(confidence)
        )
        for name, category, confidence in rows
    ]


def _detail_response(
    session: Session, candidate_id: UUID, repository: GitHubRepository
) -> GitHubRepositoryDetailResponse:
    snapshot = _get_snapshot(session, repository.id)
    base = _repository_response(session, repository)
    return GitHubRepositoryDetailResponse(
        **base.model_dump(),
        snapshot=_snapshot_summary(snapshot) if snapshot is not None else None,
        skills=_repository_skills(session, candidate_id, repository.repository_url),
    )


@router.get("/repositories", response_model=list[GitHubRepositoryResponse])
def list_repositories(
    current_user: Annotated[User, Depends(require_candidate)],
    session: Annotated[Session, Depends(get_db)],
) -> list[GitHubRepositoryResponse]:
    profile = get_candidate_profile(session, current_user.id)
    if profile is None:
        return []
    repositories = (
        session.execute(
            select(GitHubRepository)
            .where(GitHubRepository.candidate_id == profile.id)
            .order_by(GitHubRepository.created_at)
        )
        .scalars()
        .all()
    )
    return [_repository_response(session, repository) for repository in repositories]


@router.post(
    "/repositories",
    response_model=GitHubRepositoryResponse,
    status_code=201,
)
def connect_repository(
    request: GitHubRepositoryConnectRequest,
    current_user: Annotated[User, Depends(require_candidate)],
    session: Annotated[Session, Depends(get_db)],
) -> GitHubRepositoryResponse:
    profile = _require_profile(session, current_user)
    try:
        repository = connect_github_repository(session, profile.id, request.repository_url)
        session.commit()
    except GitHubRepositoryUrlError:
        session.rollback()
        raise api_error(
            422,
            "VALIDATION_ERROR",
            "Validation error",
            details=[{"field": "repository_url", "issue": "invalid_github_repository_url"}],
        ) from None
    except GitHubRepositoryConflictError:
        session.rollback()
        raise api_error(
            409,
            "GITHUB_REPOSITORY_CONFLICT",
            "A different GitHub repository is already connected",
        ) from None
    except SQLAlchemyError:
        session.rollback()
        raise api_error(500, "DATABASE_ERROR", "Database operation failed") from None
    return _repository_response(session, repository)


@router.get(
    "/repositories/{repository_id}",
    response_model=GitHubRepositoryDetailResponse,
)
def get_repository(
    repository_id: UUID,
    current_user: Annotated[User, Depends(require_candidate)],
    session: Annotated[Session, Depends(get_db)],
) -> GitHubRepositoryDetailResponse:
    profile = _require_profile(session, current_user)
    repository = _get_owned_repository(session, profile.id, repository_id)
    return _detail_response(session, profile.id, repository)


@router.post(
    "/repositories/{repository_id}/analyze",
    response_model=JobPollingResponse,
    status_code=202,
)
def analyze_repository(
    repository_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(require_candidate)],
    session: Annotated[Session, Depends(get_db)],
) -> JobPollingResponse:
    profile = _require_profile(session, current_user)
    repository = _get_owned_repository(session, profile.id, repository_id)
    try:
        result = request_github_scan(
            session, candidate_id=profile.id, repository_id=repository.id
        )
    except SQLAlchemyError:
        session.rollback()
        raise api_error(500, "DATABASE_ERROR", "Database operation failed") from None
    if result.created and result.job.status == JobStatus.PENDING:
        background_tasks.add_task(run_github_scan_job_task, result.job.id)
    return _job_response(result.job)


@router.delete("/repositories/{repository_id}", status_code=204)
def delete_repository(
    repository_id: UUID,
    current_user: Annotated[User, Depends(require_candidate)],
    session: Annotated[Session, Depends(get_db)],
) -> Response:
    profile = _require_profile(session, current_user)
    try:
        deleted = disconnect_github_repository(session, profile.id, repository_id)
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise api_error(500, "DATABASE_ERROR", "Database operation failed") from None
    if not deleted:
        raise api_error(404, "GITHUB_REPOSITORY_NOT_FOUND", "GitHub repository not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
