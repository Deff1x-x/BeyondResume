from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import require_candidate
from app.api.errors import api_error
from app.db.session import get_db
from app.main import app
from app.models.resume import Resume
from app.models.user import User


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

    async def upload(*_args: object) -> Resume:
        return uploaded

    monkeypatch.setattr(resume, "upload_resume", upload)
    response = client.post(
        "/api/v1/candidate/resume", files={"file": (filename, b"content", mime_type)}
    )

    assert response.status_code == 201
    assert set(response.json()) == {
        "id",
        "original_filename",
        "mime_type",
        "file_size_bytes",
        "parse_status",
        "created_at",
    }


def test_resume_upload_profile_required(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1 import resume
    from app.services.resume import CandidateProfileRequiredError

    authorize_candidate(make_user())

    async def upload(*_args: object) -> Resume:
        raise CandidateProfileRequiredError

    monkeypatch.setattr(resume, "upload_resume", upload)
    response = client.post(
        "/api/v1/candidate/resume", files={"file": ("resume.pdf", b"content", "application/pdf")}
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CANDIDATE_PROFILE_REQUIRED"


@pytest.mark.parametrize(
    "error_name, status_code, code",
    [
        ("UnsupportedResumeTypeError", 415, "UNSUPPORTED_RESUME_TYPE"),
        ("ResumeFileTooLargeError", 413, "RESUME_FILE_TOO_LARGE"),
        ("EmptyResumeFileError", 422, "VALIDATION_ERROR"),
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

    async def upload(*_args: object) -> Resume:
        raise error_type

    monkeypatch.setattr(resume, "upload_resume", upload)
    response = client.post(
        "/api/v1/candidate/resume", files={"file": ("resume.pdf", b"content", "application/pdf")}
    )

    assert response.status_code == status_code
    assert response.json()["error"]["code"] == code


def test_resume_upload_missing_file_and_openapi(client: TestClient) -> None:
    authorize_candidate(make_user())
    missing = client.post("/api/v1/candidate/resume")
    operations = client.get("/openapi.json").json()["paths"]["/api/v1/candidate/resume"]

    assert missing.status_code == 422
    assert missing.json()["error"]["code"] == "VALIDATION_ERROR"
    assert set(operations) == {"post"}
    assert "multipart/form-data" in str(operations)


def test_resume_upload_requires_bearer_token(client: TestClient) -> None:
    response = client.post(
        "/api/v1/candidate/resume", files={"file": ("resume.pdf", b"content", "application/pdf")}
    )

    assert response.status_code == 401


def test_resume_upload_rejects_employer(client: TestClient) -> None:
    app.dependency_overrides[require_candidate] = lambda: (_ for _ in ()).throw(
        api_error(403, "FORBIDDEN", "Candidate role required")
    )

    response = client.post(
        "/api/v1/candidate/resume", files={"file": ("resume.pdf", b"content", "application/pdf")}
    )

    assert response.status_code == 403
