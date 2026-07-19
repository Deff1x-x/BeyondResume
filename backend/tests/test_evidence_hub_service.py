from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from app.models.evidence_unit import EvidenceUnit
from app.models.resume import Resume
from app.services.evidence_hub import (
    EvidenceHubQuery,
    _preview_description,
    _source_metadata,
    list_candidate_evidence,
)


def _unit(
    *,
    candidate_id,
    source_type: str,
    source_reference: str | None,
    title: str,
    description: str | None = None,
    verification_status: str = "unverified",
    strength: str = "1.00",
    updated_at: datetime | None = None,
) -> EvidenceUnit:
    now = updated_at or datetime.now(UTC)
    return EvidenceUnit(
        id=uuid4(),
        candidate_id=candidate_id,
        source_type=source_type,
        source_reference=source_reference,
        title=title,
        description=description,
        verification_status=verification_status,
        strength_score=Decimal(strength),
        created_at=now,
        updated_at=now,
        raw_payload_reference="internal://should-not-leak",
        quality_flags={"internal": True},
    )


def test_preview_description_truncates() -> None:
    long = "x" * 400
    preview = _preview_description(long)
    assert preview is not None
    assert preview.endswith("…")
    assert len(preview) < 300


def test_source_metadata_resume_and_github() -> None:
    resume_id = uuid4()
    resume = Resume(
        id=resume_id,
        candidate_id=uuid4(),
        original_filename="backend-cv.pdf",
        stored_path="/secret/path/backend-cv.pdf",
        mime_type="application/pdf",
        file_size_bytes=100,
        is_current=True,
        extracted_text="SECRET EXTRACTED TEXT",
        parse_status="parsed",
        parsed_at=datetime(2026, 7, 1, tzinfo=UTC),
    )
    resume_unit = _unit(
        candidate_id=resume.candidate_id,
        source_type="resume",
        source_reference=str(resume_id),
        title="Backend Developer CV",
    )
    github_unit = _unit(
        candidate_id=resume.candidate_id,
        source_type="github_repository",
        source_reference="https://github.com/demo-user/demo-api",
        title="E-commerce API",
    )

    resume_source = _source_metadata(resume_unit, {resume_id: resume})
    github_source = _source_metadata(github_unit, {})

    assert resume_source.label == "Resume"
    assert resume_source.document_name == "backend-cv.pdf"
    assert resume_source.parsed_at == resume.parsed_at
    assert resume_source.model_dump().get("stored_path") is None

    assert github_source.label == "GitHub"
    assert github_source.repository_name == "demo-user/demo-api"
    assert github_source.repository_url == "https://github.com/demo-user/demo-api"


def test_list_candidate_evidence_mixed_sources_and_skills() -> None:
    candidate_id = uuid4()
    other_candidate_id = uuid4()
    resume_id = uuid4()
    skill_id = uuid4()
    now = datetime.now(UTC)

    own_resume = _unit(
        candidate_id=candidate_id,
        source_type="resume",
        source_reference=str(resume_id),
        title="Backend Developer CV",
        description="Backend engineer with experience in Python",
        updated_at=now,
    )
    own_github = _unit(
        candidate_id=candidate_id,
        source_type="github_repository",
        source_reference="https://github.com/demo-user/demo-api",
        title="E-commerce API",
        description="API service",
        verification_status="source_reachable",
        updated_at=now,
    )
    # Contaminant that must never be returned by a correctly filtered query.
    _foreign = _unit(
        candidate_id=other_candidate_id,
        source_type="resume",
        source_reference=str(uuid4()),
        title="Foreign CV",
    )

    resume = Resume(
        id=resume_id,
        candidate_id=candidate_id,
        original_filename="backend-cv.pdf",
        stored_path="/private/storage/backend-cv.pdf",
        mime_type="application/pdf",
        file_size_bytes=2048,
        is_current=True,
        extracted_text="FULL RESUME TEXT MUST NOT LEAK",
        parse_status="parsed",
        parsed_at=now,
    )

    session = Mock()
    session.execute.side_effect = [
        SimpleNamespace(scalar_one=lambda: 2),
        SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [own_resume, own_github])),
        SimpleNamespace(
            all=lambda: [
                (
                    own_resume.id,
                    skill_id,
                    "Python",
                    "backend",
                    "deterministic",
                    Decimal("1.00"),
                ),
                (
                    own_github.id,
                    skill_id,
                    "Python",
                    "backend",
                    "deterministic",
                    Decimal("0.90"),
                ),
            ]
        ),
        SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [resume])),
    ]

    result = list_candidate_evidence(
        session, candidate_id, EvidenceHubQuery(limit=20, offset=0)
    )

    assert result.total == 2
    assert len(result.items) == 2
    assert {item.source_type for item in result.items} == {"resume", "github_repository"}
    assert all(item.id in {own_resume.id, own_github.id} for item in result.items)

    resume_item = next(item for item in result.items if item.source_type == "resume")
    assert resume_item.skills[0].name == "Python"
    assert resume_item.source.document_name == "backend-cv.pdf"
    payload = resume_item.model_dump()
    assert "extracted_text" not in payload
    assert "raw_payload_reference" not in payload
    assert "quality_flags" not in payload
    assert "stored_path" not in payload
    assert resume.extracted_text not in str(payload)
    assert resume.stored_path not in str(payload)

    github_item = next(
        item for item in result.items if item.source_type == "github_repository"
    )
    assert github_item.source.repository_name == "demo-user/demo-api"
    assert github_item.skills[0].evidence_confidence == 0.9


def test_list_candidate_evidence_empty() -> None:
    session = Mock()
    session.execute.side_effect = [
        SimpleNamespace(scalar_one=lambda: 0),
        SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [])),
    ]

    result = list_candidate_evidence(
        session, uuid4(), EvidenceHubQuery(limit=10, offset=0)
    )

    assert result.items == []
    assert result.total == 0
    assert result.limit == 10


def test_list_candidate_evidence_pagination_clamped() -> None:
    session = Mock()
    session.execute.side_effect = [
        SimpleNamespace(scalar_one=lambda: 50),
        SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [])),
    ]

    result = list_candidate_evidence(
        session, uuid4(), EvidenceHubQuery(limit=500, offset=-5)
    )

    assert result.limit == 100
    assert result.offset == 0
    assert result.total == 50


def test_list_candidate_evidence_search_filter_issues_query() -> None:
    session = Mock()
    session.execute.side_effect = [
        SimpleNamespace(scalar_one=lambda: 0),
        SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [])),
    ]

    result = list_candidate_evidence(
        session, uuid4(), EvidenceHubQuery(search="python api")
    )

    assert result.total == 0
    assert session.execute.call_count == 2


def test_list_candidate_evidence_source_type_alias_github() -> None:
    candidate_id = uuid4()
    unit = _unit(
        candidate_id=candidate_id,
        source_type="github_repository",
        source_reference="https://github.com/a/b",
        title="Repo",
    )
    session = Mock()
    session.execute.side_effect = [
        SimpleNamespace(scalar_one=lambda: 1),
        SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [unit])),
        SimpleNamespace(all=lambda: []),
    ]

    result = list_candidate_evidence(
        session, candidate_id, EvidenceHubQuery(source_type="github")
    )

    assert len(result.items) == 1
    assert result.items[0].source_type == "github_repository"
    # Ensure the count/list queries were issued (filter applied in SQL, not post-filter).
    assert session.execute.call_count == 3
