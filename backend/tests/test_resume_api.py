from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.api.dependencies import require_candidate
from app.api.errors import api_error
from app.core.config import settings
from app.db.session import get_db
from app.models.candidate_profile import CandidateProfile
from app.models.job import Job, JobStatus, JobType
from app.main import app
from app.models.resume import Resume
from app.models.user import User
from app.services.resume import ResumeUploadResult


def make_user(role: str = "candidate") -> User:
    return User(
        id=uuid4(), email="candidate@example.com", password_hash="hash", role=role, status="active"
    )


def make_resume() -> Resume:
    return Resume(
        id=uuid4(),
        candidate_id=uuid4(),
        original_filename="resume.pdf",
        stored_path="/private/resume.pdf",
        mime_type="application/pdf",
        file_size_bytes=8,
        extracted_text=None,
        parse_status="uploaded",
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = lambda: object()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def authorize_candidate(user: User) -> None:
    app.dependency_overrides[require_candidate] = lambda: user


@pytest.mark.parametrize(
    ("filename", "mime_type"),
    [
        ("resume.pdf", "application/pdf"),
        ("CV.DOCX", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ],
)
def test_resume_upload_success_contract(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, filename: str, mime_type: str
) -> None:
    from app.api.v1 import resume

    authorize_candidate(make_user())
    uploaded = make_resume()
    uploaded.original_filename = filename
    uploaded.mime_type = mime_type

    job = Job(
        id=uuid4(),
        resume_id=uploaded.id,
        job_type=JobType.RESUME_PARSE,
        status=JobStatus.PENDING,
    )

    async def upload(*_args: object) -> ResumeUploadResult:
        return ResumeUploadResult(resume=uploaded, job=job)

    monkeypatch.setattr(resume, "upload_resume", upload)
    worker_calls: list[tuple[object, ...]] = []

    async def run_worker(*args: object) -> None:
        worker_calls.append(args)

    monkeypatch.setattr(resume, "run_resume_parse_job_task", run_worker)
    response = client.post(
        "/api/v1/candidate/resumes", files={"file": (filename, b"content", mime_type)}
    )

    assert response.status_code == 202
    assert response.json() == {"resume_id": str(uploaded.id), "job_id": str(job.id)}
    assert worker_calls == [(job.id,)]


def test_resume_upload_profile_required(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import resume
    from app.services.resume import CandidateProfileRequiredError

    authorize_candidate(make_user())

    async def upload(*_args: object) -> ResumeUploadResult:
        raise CandidateProfileRequiredError

    monkeypatch.setattr(resume, "upload_resume", upload)
    response = client.post(
        "/api/v1/candidate/resumes", files={"file": ("resume.pdf", b"content", "application/pdf")}
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CANDIDATE_PROFILE_REQUIRED"


@pytest.mark.parametrize(
    "error_name, status_code, code",
    [
        ("UnsupportedResumeTypeError", 415, "UNSUPPORTED_RESUME_TYPE"),
        ("ResumeFileTooLargeError", 413, "RESUME_FILE_TOO_LARGE"),
        ("EmptyResumeFileError", 422, "VALIDATION_ERROR"),
        ("InvalidResumeContentError", 422, "VALIDATION_ERROR"),
    ],
)
def test_resume_upload_error_mapping(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    error_name: str,
    status_code: int,
    code: str,
) -> None:
    from app.api.v1 import resume
    from app.services import resume as resume_service

    authorize_candidate(make_user())
    error_type = getattr(resume_service, error_name)

    async def upload(*_args: object) -> ResumeUploadResult:
        raise error_type

    monkeypatch.setattr(resume, "upload_resume", upload)
    response = client.post(
        "/api/v1/candidate/resumes", files={"file": ("resume.pdf", b"content", "application/pdf")}
    )

    assert response.status_code == status_code
    assert response.json()["error"]["code"] == code


@pytest.mark.parametrize(
    ("filename", "mime_type", "content"),
    [
        ("resume.pdf", "application/pdf", b"not a PDF"),
        (
            "resume.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            b"not a DOCX archive",
        ),
    ],
)
def test_resume_upload_rejects_malformed_content_without_persistence_or_scheduling(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    filename: str,
    mime_type: str,
    content: bytes,
) -> None:
    from app.api.v1 import resume as resume_api

    candidate = make_user()
    authorize_candidate(candidate)
    profile = CandidateProfile(
        id=uuid4(),
        user_id=candidate.id,
        display_name="Candidate",
        onboarding_status="profile_completed",
    )
    session = Mock()
    session.execute.return_value.scalar_one_or_none.return_value = profile
    app.dependency_overrides[get_db] = lambda: session
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    worker_calls: list[tuple[object, ...]] = []

    async def run_worker(*args: object) -> None:
        worker_calls.append(args)

    monkeypatch.setattr(resume_api, "run_resume_parse_job_task", run_worker)

    response = client.post(
        "/api/v1/candidate/resumes", files={"file": (filename, content, mime_type)}
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"] == "Validation error"
    assert body["error"]["details"] == [{"field": "file", "issue": "corrupted_file"}]
    assert "BadZipFile" not in str(body)
    assert "InvalidResumeContentError" not in str(body)
    session.add.assert_not_called()
    session.commit.assert_not_called()
    assert list(tmp_path.iterdir()) == []
    assert worker_calls == []


def test_resume_upload_missing_file_and_openapi(client: TestClient) -> None:
    authorize_candidate(make_user())
    missing = client.post("/api/v1/candidate/resumes")
    openapi = client.get("/openapi.json").json()
    paths = openapi["paths"]
    operations = paths["/api/v1/candidate/resumes"]

    assert missing.status_code == 422
    assert missing.json()["error"]["code"] == "VALIDATION_ERROR"
    assert set(operations) == {"get", "post"}
    assert "multipart/form-data" in str(operations)
    response_schema = operations["post"]["responses"]["202"]["content"]["application/json"][
        "schema"
    ]
    assert response_schema["$ref"].endswith("/ResumeUploadAcceptedResponse")
    schema = openapi["components"]["schemas"]["ResumeUploadAcceptedResponse"]
    assert set(schema["properties"]) == {"resume_id", "job_id"}
    assert set(schema["required"]) == {"resume_id", "job_id"}
    assert {field["format"] for field in schema["properties"].values()} == {"uuid"}
    assert "/api/v1/candidate/resume" not in paths


def test_resume_member_read_uses_plural_path(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import resume as resume_api
    from app.schemas.resume import ResumeResponse

    candidate = make_user()
    resume = make_resume()
    authorize_candidate(candidate)
    monkeypatch.setattr(resume_api, "get_candidate_resume", lambda *_args: resume)
    monkeypatch.setattr(
        resume_api,
        "build_resume_response",
        lambda _session, value: ResumeResponse(
            id=value.id,
            original_filename=value.original_filename,
            mime_type=value.mime_type,
            file_size=value.file_size,
            status=value.parse_status,  # type: ignore[arg-type]
            uploaded_at=value.created_at,
        ),
    )

    response = client.get(f"/api/v1/candidate/resumes/{resume.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(resume.id)
    assert response.json()["evidence_id"] is None


def test_resume_upload_requires_bearer_token(client: TestClient) -> None:
    response = client.post(
        "/api/v1/candidate/resumes", files={"file": ("resume.pdf", b"content", "application/pdf")}
    )

    assert response.status_code == 401


def test_resume_upload_rejects_employer(client: TestClient) -> None:
    app.dependency_overrides[require_candidate] = lambda: (_ for _ in ()).throw(
        api_error(403, "FORBIDDEN", "Candidate role required")
    )

    response = client.post(
        "/api/v1/candidate/resumes", files={"file": ("resume.pdf", b"content", "application/pdf")}
    )

    assert response.status_code == 403


def test_job_polling_returns_only_safe_lifecycle_fields(client: TestClient) -> None:
    candidate = make_user()
    authorize_candidate(candidate)
    resume = make_resume()
    resume.parse_status = "failed"
    job = Job(
        id=uuid4(),
        resume_id=resume.id,
        job_type=JobType.RESUME_PARSE,
        status=JobStatus.FAILED,
        created_at=datetime.now(UTC),
        error_code="RESUME_FILE_MISSING",
        error_message="Resume file is unavailable",
    )
    session = Mock()
    session.execute.side_effect = [
        SimpleNamespace(scalar_one_or_none=lambda: job),
        SimpleNamespace(scalar_one_or_none=lambda: resume),
        SimpleNamespace(scalar_one_or_none=lambda: None),
    ]
    app.dependency_overrides[get_db] = lambda: session

    response = client.get(f"/api/v1/jobs/{job.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert body["job_type"] == "resume_parse"
    assert body["resume_status"] == "failed"
    assert body["retry_available"] is True
    assert "storage_path" not in body
    assert "checksum" not in body
    assert "extracted_text" not in body
    assert "resume_id" not in body


def test_job_polling_returns_typed_not_found_for_other_candidate(client: TestClient) -> None:
    authorize_candidate(make_user())
    session = type(
        "Session",
        (),
        {"execute": lambda *_args: type("Result", (), {"scalar_one_or_none": lambda _: None})()},
    )()
    app.dependency_overrides[get_db] = lambda: session

    response = client.get(f"/api/v1/jobs/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "JOB_NOT_FOUND"


def test_job_polling_requires_authentication(client: TestClient) -> None:
    response = client.get(f"/api/v1/jobs/{uuid4()}")

    assert response.status_code == 401


def test_job_polling_rejects_employer(client: TestClient) -> None:
    app.dependency_overrides[require_candidate] = lambda: (_ for _ in ()).throw(
        api_error(403, "FORBIDDEN", "Candidate role required")
    )

    response = client.get(f"/api/v1/jobs/{uuid4()}")

    assert response.status_code == 403


def test_resume_retry_returns_new_pending_job(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import resume as resume_api
    from app.services.resume_jobs import ResumeRetryResult

    candidate = make_user()
    authorize_candidate(candidate)
    failed_resume = make_resume()
    failed_resume.parse_status = "failed"
    job = Job(
        id=uuid4(),
        resume_id=failed_resume.id,
        job_type=JobType.RESUME_PARSE,
        status=JobStatus.PENDING,
        created_at=datetime.now(UTC),
    )
    monkeypatch.setattr(resume_api, "get_current_resume", lambda *_args: failed_resume)

    def retry(*_args: object) -> ResumeRetryResult:
        failed_resume.parse_status = "uploaded"
        return ResumeRetryResult(job=job, should_schedule=True)

    monkeypatch.setattr(resume_api, "retry_failed_resume", retry)
    worker_calls: list[tuple[object, ...]] = []

    async def run_worker(*args: object) -> None:
        worker_calls.append(args)

    monkeypatch.setattr(resume_api, "run_resume_parse_job_task", run_worker)

    response = client.post("/api/v1/candidate/resume/retry")

    assert response.status_code == 201
    assert response.json()["status"] == "pending"
    assert response.json()["resume_status"] == "uploaded"
    assert worker_calls == [(job.id,)]


def test_resume_retry_returns_active_job_without_scheduling_worker(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import resume as resume_api
    from app.services.resume_jobs import ResumeRetryResult

    authorize_candidate(make_user())
    failed_resume = make_resume()
    failed_resume.parse_status = "failed"
    active = Job(
        id=uuid4(),
        resume_id=failed_resume.id,
        job_type=JobType.RESUME_PARSE,
        status=JobStatus.RUNNING,
        created_at=datetime.now(UTC),
        started_at=datetime.now(UTC),
    )
    monkeypatch.setattr(resume_api, "get_current_resume", lambda *_args: failed_resume)
    monkeypatch.setattr(
        resume_api,
        "retry_failed_resume",
        lambda *_args: ResumeRetryResult(job=active, should_schedule=False),
    )
    worker_calls: list[tuple[object, ...]] = []

    async def run_worker(*args: object) -> None:
        worker_calls.append(args)

    monkeypatch.setattr(resume_api, "run_resume_parse_job_task", run_worker)

    response = client.post("/api/v1/candidate/resume/retry")

    assert response.status_code == 201
    assert response.json()["id"] == str(active.id)
    assert response.json()["status"] == "running"
    assert worker_calls == []


def test_resume_retry_service_error_does_not_schedule_worker(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import resume as resume_api

    authorize_candidate(make_user())
    failed_resume = make_resume()
    failed_resume.parse_status = "failed"
    session = Mock()
    app.dependency_overrides[get_db] = lambda: session
    monkeypatch.setattr(resume_api, "get_current_resume", lambda *_args: failed_resume)

    def retry(*_args: object) -> Job:
        raise SQLAlchemyError("database failure")

    monkeypatch.setattr(resume_api, "retry_failed_resume", retry)
    worker_calls: list[tuple[object, ...]] = []

    async def run_worker(*args: object) -> None:
        worker_calls.append(args)

    monkeypatch.setattr(resume_api, "run_resume_parse_job_task", run_worker)

    response = client.post("/api/v1/candidate/resume/retry")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "DATABASE_ERROR"
    assert worker_calls == []
    session.rollback.assert_called_once()


def test_resume_retry_rejects_non_failed_current_resume(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import resume as resume_api
    from app.services.resume_jobs import ResumeTransitionError

    authorize_candidate(make_user())
    monkeypatch.setattr(resume_api, "get_current_resume", lambda *_args: make_resume())

    def retry(*_args: object) -> Job:
        raise ResumeTransitionError

    monkeypatch.setattr(resume_api, "retry_failed_resume", retry)
    response = client.post("/api/v1/candidate/resume/retry")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "RESUME_RETRY_NOT_ALLOWED"


def test_resume_retry_returns_not_found_without_current_resume(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import resume as resume_api

    authorize_candidate(make_user())
    monkeypatch.setattr(resume_api, "get_current_resume", lambda *_args: None)

    response = client.post("/api/v1/candidate/resume/retry")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESUME_NOT_FOUND"


def test_resume_retry_requires_authentication(client: TestClient) -> None:
    response = client.post("/api/v1/candidate/resume/retry")

    assert response.status_code == 401


def test_resume_retry_rejects_employer(client: TestClient) -> None:
    app.dependency_overrides[require_candidate] = lambda: (_ for _ in ()).throw(
        api_error(403, "FORBIDDEN", "Candidate role required")
    )

    response = client.post("/api/v1/candidate/resume/retry")

    assert response.status_code == 403


def test_parse_request_creates_orchestrated_job_without_text(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import resume as resume_api

    candidate = make_user()
    authorize_candidate(candidate)
    resume = make_resume()
    job = Job(
        id=uuid4(),
        resume_id=resume.id,
        job_type=JobType.RESUME_PARSE,
        status=JobStatus.PENDING,
        created_at=datetime.now(UTC),
    )
    monkeypatch.setattr(resume_api, "get_candidate_resume", lambda *_args: resume)
    monkeypatch.setattr(resume_api, "request_resume_parse", lambda *_args: job)
    worker_calls: list[object] = []

    async def run_worker(*args: object) -> None:
        worker_calls.append(args)

    monkeypatch.setattr(resume_api, "run_resume_parse_job_task", run_worker)

    response = client.post(f"/api/v1/candidate/resumes/{resume.id}/parse")

    assert response.status_code == 200
    assert response.json()["id"] == str(job.id)
    assert response.json()["status"] == "pending"
    assert "extracted_text" not in response.json()
    assert worker_calls == [(job.id,)]


def test_parse_request_is_idempotent_for_active_job(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import resume as resume_api

    authorize_candidate(make_user())
    resume = make_resume()
    active = Job(
        id=uuid4(),
        resume_id=resume.id,
        job_type=JobType.RESUME_PARSE,
        status=JobStatus.RUNNING,
        created_at=datetime.now(UTC),
        started_at=datetime.now(UTC),
    )
    monkeypatch.setattr(resume_api, "get_candidate_resume", lambda *_args: resume)
    monkeypatch.setattr(resume_api, "request_resume_parse", lambda *_args: active)

    response = client.post(f"/api/v1/candidate/resumes/{resume.id}/parse")

    assert response.status_code == 200
    assert response.json()["id"] == str(active.id)
    assert response.json()["status"] == "running"


def test_parse_request_returns_not_found_for_other_candidate(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import resume as resume_api

    authorize_candidate(make_user())
    monkeypatch.setattr(resume_api, "get_candidate_resume", lambda *_args: None)

    response = client.post(f"/api/v1/candidate/resumes/{uuid4()}/parse")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESUME_NOT_FOUND"


def test_parse_endpoint_openapi_does_not_expose_extracted_text(client: TestClient) -> None:
    operation = client.get("/openapi.json").json()["paths"][
        "/api/v1/candidate/resumes/{resume_id}/parse"
    ]

    assert set(operation) == {"post"}
    assert "extracted_text" not in str(operation)
