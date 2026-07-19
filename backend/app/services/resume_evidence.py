"""Create EvidenceUnit rows from a successfully parsed Resume.

Skill linking is performed by the shared SkillExtractionService after this
upsert returns, not inside this module.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evidence_unit import EvidenceUnit
from app.models.resume import Resume

RESUME_EVIDENCE_SOURCE_TYPE = "resume"
_DESCRIPTION_PREVIEW_CHARS = 2_000


@dataclass(frozen=True, slots=True)
class ResumeEvidenceGenerationResult:
    evidence_unit: EvidenceUnit
    created: bool
    changed: bool


def resume_source_reference(resume_id: UUID) -> str:
    return str(resume_id)


def generate_resume_evidence(session: Session, resume: Resume) -> ResumeEvidenceGenerationResult:
    """Upsert EvidenceUnit for a resume that already has extracted_text set."""
    if not resume.extracted_text or not resume.extracted_text.strip():
        raise ValueError("Resume evidence requires non-empty extracted text")

    managed_fields = _managed_evidence_fields(resume)
    source_reference = managed_fields["source_reference"]
    assert isinstance(source_reference, str)

    evidence_unit = session.execute(
        select(EvidenceUnit).where(
            EvidenceUnit.candidate_id == resume.candidate_id,
            EvidenceUnit.source_type == RESUME_EVIDENCE_SOURCE_TYPE,
            EvidenceUnit.source_reference == source_reference,
        )
    ).scalar_one_or_none()

    if evidence_unit is None:
        evidence_unit = EvidenceUnit(candidate_id=resume.candidate_id, **managed_fields)
        session.add(evidence_unit)
        session.flush()
        return ResumeEvidenceGenerationResult(
            evidence_unit=evidence_unit, created=True, changed=True
        )

    if all(getattr(evidence_unit, field) == value for field, value in managed_fields.items()):
        return ResumeEvidenceGenerationResult(
            evidence_unit=evidence_unit, created=False, changed=False
        )

    for field, value in managed_fields.items():
        setattr(evidence_unit, field, value)
    session.flush()
    return ResumeEvidenceGenerationResult(
        evidence_unit=evidence_unit, created=False, changed=True
    )


def get_resume_evidence(session: Session, resume_id: UUID) -> EvidenceUnit | None:
    return session.execute(
        select(EvidenceUnit).where(
            EvidenceUnit.source_type == RESUME_EVIDENCE_SOURCE_TYPE,
            EvidenceUnit.source_reference == resume_source_reference(resume_id),
        )
    ).scalar_one_or_none()


def _managed_evidence_fields(resume: Resume) -> dict[str, object]:
    text = (resume.extracted_text or "").strip()
    preview = text[:_DESCRIPTION_PREVIEW_CHARS]
    if len(text) > _DESCRIPTION_PREVIEW_CHARS:
        preview = f"{preview}…"
    observed_at = resume.parsed_at or datetime.now(UTC)
    title = f"Resume: {resume.original_filename}"
    return {
        "source_type": RESUME_EVIDENCE_SOURCE_TYPE,
        "source_reference": resume_source_reference(resume.id),
        "title": title[:255],
        "description": preview,
        "observed_at": observed_at,
        "issued_at": None,
        "freshness_at": observed_at,
        "verification_status": "unverified",
        "ownership_status": "unverified",
        "strength_score": Decimal("1.00"),
        "quality_flags": {
            "pdf": resume.mime_type == "application/pdf",
            "has_extracted_text": bool(text),
            "truncated_description": len(text) > _DESCRIPTION_PREVIEW_CHARS,
        },
        # Points at the Resume row that owns the full extracted text.
        "raw_payload_reference": f"resume:{resume.id}",
    }
