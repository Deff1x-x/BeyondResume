from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.models.evidence_unit import EvidenceUnit
from app.models.resume import Resume
from app.services.resume_evidence import (
    RESUME_EVIDENCE_SOURCE_TYPE,
    generate_resume_evidence,
    resume_source_reference,
)


def make_resume(*, text: str = "Python\nFastAPI experience") -> Resume:
    return Resume(
        id=uuid4(),
        candidate_id=uuid4(),
        original_filename="resume.pdf",
        stored_path="safe.pdf",
        mime_type="application/pdf",
        file_size_bytes=12,
        extracted_text=text,
        parse_status="uploaded",
        parsed_at=datetime(2026, 7, 20, tzinfo=UTC),
    )


def make_session(existing: EvidenceUnit | None = None) -> Mock:
    session = Mock()
    result = Mock()
    result.scalar_one_or_none.return_value = existing
    session.execute.return_value = result
    return session


def test_generate_resume_evidence_creates_unit() -> None:
    resume = make_resume()
    session = make_session()

    result = generate_resume_evidence(session, resume)

    assert result.created is True
    assert result.changed is True
    session.add.assert_called_once()
    evidence = session.add.call_args.args[0]
    assert isinstance(evidence, EvidenceUnit)
    assert evidence.candidate_id == resume.candidate_id
    assert evidence.source_type == RESUME_EVIDENCE_SOURCE_TYPE
    assert evidence.source_reference == resume_source_reference(resume.id)
    assert evidence.title == "Resume: resume.pdf"
    assert evidence.description == "Python\nFastAPI experience"
    assert evidence.verification_status == "unverified"
    assert evidence.ownership_status == "unverified"
    assert evidence.strength_score == Decimal("1.00")
    assert evidence.raw_payload_reference == f"resume:{resume.id}"
    assert evidence.quality_flags == {
        "pdf": True,
        "has_extracted_text": True,
        "truncated_description": False,
    }
    session.flush.assert_called_once()


def test_generate_resume_evidence_is_idempotent() -> None:
    resume = make_resume()
    existing = EvidenceUnit(
        id=uuid4(),
        candidate_id=resume.candidate_id,
        source_type=RESUME_EVIDENCE_SOURCE_TYPE,
        source_reference=resume_source_reference(resume.id),
        title="Resume: resume.pdf",
        description="Python\nFastAPI experience",
        observed_at=resume.parsed_at,
        issued_at=None,
        freshness_at=resume.parsed_at,
        verification_status="unverified",
        ownership_status="unverified",
        strength_score=Decimal("1.00"),
        quality_flags={
            "pdf": True,
            "has_extracted_text": True,
            "truncated_description": False,
        },
        raw_payload_reference=f"resume:{resume.id}",
    )
    session = make_session(existing)

    result = generate_resume_evidence(session, resume)

    assert result.created is False
    assert result.changed is False
    assert result.evidence_unit is existing
    session.add.assert_not_called()
    session.flush.assert_not_called()


def test_generate_resume_evidence_updates_changed_fields() -> None:
    resume = make_resume(text="Updated resume body")
    existing = EvidenceUnit(
        id=uuid4(),
        candidate_id=resume.candidate_id,
        source_type=RESUME_EVIDENCE_SOURCE_TYPE,
        source_reference=resume_source_reference(resume.id),
        title="Resume: resume.pdf",
        description="old",
        observed_at=resume.parsed_at,
        issued_at=None,
        freshness_at=resume.parsed_at,
        verification_status="unverified",
        ownership_status="unverified",
        strength_score=Decimal("1.00"),
        quality_flags={
            "pdf": True,
            "has_extracted_text": True,
            "truncated_description": False,
        },
        raw_payload_reference=f"resume:{resume.id}",
    )
    session = make_session(existing)

    result = generate_resume_evidence(session, resume)

    assert result.created is False
    assert result.changed is True
    assert existing.description == "Updated resume body"
    session.flush.assert_called_once()


def test_generate_resume_evidence_rejects_empty_text() -> None:
    resume = make_resume(text="   ")
    with pytest.raises(ValueError, match="non-empty extracted text"):
        generate_resume_evidence(make_session(), resume)
