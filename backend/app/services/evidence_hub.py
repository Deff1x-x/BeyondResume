"""Read-only Candidate Evidence Hub over EvidenceUnit + EvidenceSkillLink.

No source-specific business logic beyond safe metadata projection.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import ColumnElement, false, func, or_, select
from sqlalchemy.orm import Session

from app.models.evidence_skill_link import EvidenceSkillLink
from app.models.evidence_unit import EvidenceUnit
from app.models.resume import Resume
from app.models.skill import Skill
from app.schemas.evidence import (
    EvidenceHubItemResponse,
    EvidenceHubListResponse,
    EvidenceHubSkillResponse,
    EvidenceHubSourceResponse,
)
from app.utils.github_url import GitHubRepositoryUrlError, parse_github_repository_url
from app.utils.skill_name import InvalidSkillNameError, normalize_skill_name

DEFAULT_LIMIT = 20
MAX_LIMIT = 100
DESCRIPTION_PREVIEW_CHARS = 280

SOURCE_TYPE_ALIASES = {
    "github": "github_repository",
    "github_repository": "github_repository",
    "resume": "resume",
}


@dataclass(frozen=True, slots=True)
class EvidenceHubQuery:
    source_type: str | None = None
    skill: str | None = None
    search: str | None = None
    limit: int = DEFAULT_LIMIT
    offset: int = 0


def list_candidate_evidence(
    session: Session, candidate_id: UUID, query: EvidenceHubQuery
) -> EvidenceHubListResponse:
    limit = min(max(query.limit, 1), MAX_LIMIT)
    offset = max(query.offset, 0)

    filters = _build_filters(session, candidate_id, query)
    base = select(EvidenceUnit).where(*filters)
    total = session.execute(select(func.count()).select_from(base.subquery())).scalar_one()

    units = list(
        session.execute(
            base.order_by(EvidenceUnit.updated_at.desc(), EvidenceUnit.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        .scalars()
        .all()
    )
    skills_by_unit = _skills_by_unit(session, [unit.id for unit in units])
    resume_meta = _resume_metadata(session, units)

    items = [
        EvidenceHubItemResponse(
            id=unit.id,
            source_type=unit.source_type,
            source_reference=unit.source_reference,
            title=unit.title,
            description=_preview_description(unit.description),
            verification_status=unit.verification_status,
            strength=float(unit.strength_score) if unit.strength_score is not None else None,
            created_at=unit.created_at,
            updated_at=unit.updated_at,
            skills=skills_by_unit.get(unit.id, []),
            source=_source_metadata(unit, resume_meta),
        )
        for unit in units
    ]
    return EvidenceHubListResponse(items=items, total=int(total), limit=limit, offset=offset)


def _build_filters(
    session: Session, candidate_id: UUID, query: EvidenceHubQuery
) -> list[ColumnElement[bool]]:
    filters: list[ColumnElement[bool]] = [EvidenceUnit.candidate_id == candidate_id]

    if query.source_type:
        normalized = SOURCE_TYPE_ALIASES.get(query.source_type.strip().lower())
        if normalized is None:
            # Unknown source types intentionally match nothing.
            filters.append(EvidenceUnit.source_type == "__none__")
        else:
            filters.append(EvidenceUnit.source_type == normalized)

    if query.search and query.search.strip():
        term = f"%{query.search.strip()}%"
        filters.append(
            or_(EvidenceUnit.title.ilike(term), EvidenceUnit.description.ilike(term))
        )

    if query.skill and query.skill.strip():
        skill_filter = _skill_filter(session, query.skill.strip())
        if skill_filter is None:
            filters.append(false())
        else:
            filters.append(skill_filter)

    return filters


def _skill_filter(session: Session, skill: str) -> ColumnElement[bool] | None:
    try:
        skill_id = UUID(skill)
    except ValueError:
        skill_id = None

    if skill_id is not None:
        return EvidenceUnit.id.in_(
            select(EvidenceSkillLink.evidence_unit_id).where(
                EvidenceSkillLink.skill_id == skill_id
            )
        )

    try:
        normalized = normalize_skill_name(skill)
    except InvalidSkillNameError:
        return None

    skill_row = session.execute(
        select(Skill.id).where(
            or_(Skill.normalized_name == normalized, Skill.canonical_name == skill)
        )
    ).scalar_one_or_none()
    if skill_row is None:
        return None
    return EvidenceUnit.id.in_(
        select(EvidenceSkillLink.evidence_unit_id).where(
            EvidenceSkillLink.skill_id == skill_row
        )
    )


def _skills_by_unit(
    session: Session, evidence_unit_ids: list[UUID]
) -> dict[UUID, list[EvidenceHubSkillResponse]]:
    if not evidence_unit_ids:
        return {}
    rows = session.execute(
        select(
            EvidenceSkillLink.evidence_unit_id,
            Skill.id,
            Skill.canonical_name,
            Skill.category,
            EvidenceSkillLink.extraction_method,
            EvidenceSkillLink.extraction_confidence,
        )
        .join(Skill, Skill.id == EvidenceSkillLink.skill_id)
        .where(EvidenceSkillLink.evidence_unit_id.in_(evidence_unit_ids))
        .order_by(Skill.canonical_name)
    ).all()
    skills: dict[UUID, list[EvidenceHubSkillResponse]] = {}
    seen: dict[UUID, set[UUID]] = {}
    for evidence_unit_id, skill_id, name, category, method, confidence in rows:
        unit_seen = seen.setdefault(evidence_unit_id, set())
        if skill_id in unit_seen:
            continue
        unit_seen.add(skill_id)
        skills.setdefault(evidence_unit_id, []).append(
            EvidenceHubSkillResponse(
                id=skill_id,
                name=name,
                category=category,
                extraction_method=method,
                evidence_confidence=float(confidence),
            )
        )
    return skills


def _resume_metadata(
    session: Session, units: list[EvidenceUnit]
) -> dict[UUID, Resume]:
    resume_ids: list[UUID] = []
    for unit in units:
        if unit.source_type != "resume" or not unit.source_reference:
            continue
        try:
            resume_ids.append(UUID(unit.source_reference))
        except ValueError:
            continue
    if not resume_ids:
        return {}
    resumes = (
        session.execute(select(Resume).where(Resume.id.in_(resume_ids))).scalars().all()
    )
    return {resume.id: resume for resume in resumes}


def _source_metadata(
    unit: EvidenceUnit, resume_meta: dict[UUID, Resume]
) -> EvidenceHubSourceResponse:
    if unit.source_type == "resume":
        resume: Resume | None = None
        if unit.source_reference:
            try:
                resume = resume_meta.get(UUID(unit.source_reference))
            except ValueError:
                resume = None
        return EvidenceHubSourceResponse(
            label="Resume",
            document_name=resume.original_filename if resume is not None else None,
            parsed_at=resume.parsed_at if resume is not None else None,
        )

    if unit.source_type == "github_repository":
        repository_url = unit.source_reference
        repository_name: str | None = None
        if repository_url:
            try:
                parsed = parse_github_repository_url(repository_url)
                repository_name = f"{parsed.owner}/{parsed.repository}"
            except GitHubRepositoryUrlError:
                repository_name = None
        return EvidenceHubSourceResponse(
            label="GitHub",
            repository_name=repository_name,
            repository_url=repository_url,
        )

    return EvidenceHubSourceResponse(label=unit.source_type.replace("_", " ").title())


def _preview_description(description: str | None) -> str | None:
    if description is None:
        return None
    text = description.strip()
    if not text:
        return None
    if len(text) <= DESCRIPTION_PREVIEW_CHARS:
        return text
    return f"{text[:DESCRIPTION_PREVIEW_CHARS].rstrip()}…"
