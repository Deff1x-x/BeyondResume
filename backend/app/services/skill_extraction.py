"""Deterministic Evidence → Skill extraction for any EvidenceUnit.

v1 matches ontology Skill.canonical_name / SkillAlias against evidence text
(title, description, and optional raw payload). No LLM.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal
from typing import Final
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.evidence_skill_link import EvidenceSkillLink
from app.models.evidence_unit import EvidenceUnit
from app.models.github_repository_snapshot import GitHubRepositorySnapshot
from app.models.resume import Resume
from app.models.skill import Skill
from app.services.evidence_skill_links import persist_evidence_skill_link

EXTRACTION_METHOD: Final = "deterministic"
EXTRACTION_VERSION: Final = "evidence-skill-v1"
_EXTRACTOR_NAME: Final = "evidence_skill_v1"
_MIN_TERM_LENGTH: Final = 2


@dataclass(frozen=True, slots=True)
class ExtractedSkillMatch:
    skill: Skill
    matched_term: str
    match_kind: str


@dataclass(frozen=True, slots=True)
class SkillExtractionResult:
    evidence_unit: EvidenceUnit
    matches: tuple[ExtractedSkillMatch, ...]
    links: tuple[EvidenceSkillLink, ...]
    created_count: int
    changed_count: int
    unchanged_count: int
    removed_count: int


class SkillExtractionService:
    """Source-agnostic skill extraction over a single EvidenceUnit."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def extract_skills(self, evidence_unit: EvidenceUnit) -> tuple[Skill, ...]:
        return tuple(match.skill for match in self.extract_matches(evidence_unit))

    def extract_matches(self, evidence_unit: EvidenceUnit) -> tuple[ExtractedSkillMatch, ...]:
        corpus = build_evidence_corpus(self._session, evidence_unit)
        if not corpus.strip():
            return ()
        return match_skills_in_text(self._session, corpus)

    def extract_and_link(self, evidence_unit: EvidenceUnit) -> SkillExtractionResult:
        matches = self.extract_matches(evidence_unit)
        return _reconcile_links(self._session, evidence_unit, matches)


def extract_and_link_evidence_skills(
    session: Session, evidence_unit: EvidenceUnit
) -> SkillExtractionResult:
    """Orchestration entry point used by GitHub and Resume job pipelines."""
    return SkillExtractionService(session).extract_and_link(evidence_unit)


def build_evidence_corpus(session: Session, evidence_unit: EvidenceUnit) -> str:
    parts: list[str] = []
    if evidence_unit.title:
        parts.append(evidence_unit.title)
    if evidence_unit.description:
        parts.append(evidence_unit.description)
    payload_text = _load_raw_payload_text(session, evidence_unit.raw_payload_reference)
    if payload_text:
        parts.append(payload_text)
    return "\n".join(parts)


def match_skills_in_text(session: Session, text: str) -> tuple[ExtractedSkillMatch, ...]:
    normalized_corpus = _normalize_corpus(text)
    if not normalized_corpus:
        return ()

    skills = session.execute(
        select(Skill)
        .where(Skill.deprecated.is_(False))
        .options(selectinload(Skill.aliases))
        .order_by(Skill.canonical_name)
    ).scalars().all()

    terms: list[tuple[str, Skill, str]] = []
    for skill in skills:
        terms.append((skill.normalized_name, skill, "canonical_name"))
        for alias in skill.aliases:
            terms.append((alias.normalized_alias, skill, "alias"))

    # Longer terms first so "machine learning" wins over a shorter overlap.
    terms.sort(key=lambda item: (-len(item[0]), item[0]))

    matched_skill_ids: set[UUID] = set()
    matches: list[ExtractedSkillMatch] = []
    for normalized_term, skill, match_kind in terms:
        if skill.id in matched_skill_ids:
            continue
        if len(normalized_term) < _MIN_TERM_LENGTH:
            continue
        if not _corpus_contains_term(normalized_corpus, normalized_term):
            continue
        matched_skill_ids.add(skill.id)
        display_term = (
            skill.canonical_name
            if match_kind == "canonical_name"
            else next(
                (
                    alias.alias
                    for alias in skill.aliases
                    if alias.normalized_alias == normalized_term
                ),
                normalized_term,
            )
        )
        matches.append(
            ExtractedSkillMatch(skill=skill, matched_term=display_term, match_kind=match_kind)
        )

    matches.sort(key=lambda item: item.skill.canonical_name.lower())
    return tuple(matches)


def _reconcile_links(
    session: Session,
    evidence_unit: EvidenceUnit,
    matches: tuple[ExtractedSkillMatch, ...],
) -> SkillExtractionResult:
    existing_links = tuple(
        session.execute(
            select(EvidenceSkillLink).where(
                EvidenceSkillLink.candidate_id == evidence_unit.candidate_id,
                EvidenceSkillLink.evidence_unit_id == evidence_unit.id,
                EvidenceSkillLink.extraction_method == EXTRACTION_METHOD,
                EvidenceSkillLink.extraction_version == EXTRACTION_VERSION,
            )
        )
        .scalars()
        .all()
    )

    persistence_results = []
    for match in matches:
        persistence_results.append(
            persist_evidence_skill_link(
                session,
                candidate_id=evidence_unit.candidate_id,
                evidence_unit=evidence_unit,
                skill=match.skill,
                extraction_method=EXTRACTION_METHOD,
                extraction_version=EXTRACTION_VERSION,
                extraction_confidence=Decimal("1.00"),
                context={
                    "extractor": _EXTRACTOR_NAME,
                    "version": EXTRACTION_VERSION,
                    "matched_term": match.matched_term,
                    "match_kind": match.match_kind,
                },
            )
        )

    links = tuple(result.link for result in persistence_results)
    desired_ids = {link.skill_id for link in links}
    stale_links = [link for link in existing_links if link.skill_id not in desired_ids]
    for stale_link in stale_links:
        session.delete(stale_link)
    if stale_links:
        session.flush()

    return SkillExtractionResult(
        evidence_unit=evidence_unit,
        matches=matches,
        links=links,
        created_count=sum(result.created and result.changed for result in persistence_results),
        changed_count=sum(not result.created and result.changed for result in persistence_results),
        unchanged_count=sum(
            not result.created and not result.changed for result in persistence_results
        ),
        removed_count=len(stale_links),
    )


def _normalize_corpus(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).lower()
    normalized = normalized.replace("_", " ").replace("-", " ")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _corpus_contains_term(normalized_corpus: str, normalized_term: str) -> bool:
    pattern = (
        r"(?<!\w)"
        + re.escape(normalized_term).replace(r"\ ", r"\s+")
        + r"(?!\w)"
    )
    return re.search(pattern, normalized_corpus) is not None


def _load_raw_payload_text(session: Session, raw_payload_reference: str | None) -> str:
    if not raw_payload_reference:
        return ""
    if raw_payload_reference.startswith("resume:"):
        return _resume_payload_text(session, raw_payload_reference.removeprefix("resume:"))
    if raw_payload_reference.startswith("github_repository_snapshot:"):
        return _github_snapshot_payload_text(
            session, raw_payload_reference.removeprefix("github_repository_snapshot:")
        )
    return ""


def _resume_payload_text(session: Session, resume_id_text: str) -> str:
    try:
        resume_id = UUID(resume_id_text)
    except ValueError:
        return ""
    resume = session.execute(select(Resume).where(Resume.id == resume_id)).scalar_one_or_none()
    if resume is None or not resume.extracted_text:
        return ""
    return resume.extracted_text


def _github_snapshot_payload_text(session: Session, snapshot_id_text: str) -> str:
    try:
        snapshot_id = UUID(snapshot_id_text)
    except ValueError:
        return ""
    snapshot = session.execute(
        select(GitHubRepositorySnapshot).where(GitHubRepositorySnapshot.id == snapshot_id)
    ).scalar_one_or_none()
    if snapshot is None or not isinstance(snapshot.payload, dict):
        return ""
    return _flatten_github_snapshot_payload(snapshot.payload)


def _flatten_github_snapshot_payload(payload: dict[str, object]) -> str:
    chunks: list[str] = []
    description = payload.get("description")
    if isinstance(description, str) and description.strip():
        chunks.append(description)
    languages = payload.get("languages")
    if isinstance(languages, list):
        chunks.extend(str(item) for item in languages if item)
    readme = payload.get("readme_text")
    if isinstance(readme, str) and readme.strip():
        chunks.append(readme)
    for key in ("tree_paths", "manifest_paths"):
        values = payload.get(key)
        if isinstance(values, list):
            chunks.extend(str(item) for item in values if item)
    manifests = payload.get("normalized_manifests")
    if isinstance(manifests, list):
        for manifest in manifests:
            if not isinstance(manifest, dict):
                continue
            dependencies = manifest.get("dependencies")
            if not isinstance(dependencies, list):
                continue
            for dependency in dependencies:
                if isinstance(dependency, dict):
                    name = dependency.get("name")
                    if isinstance(name, str) and name.strip():
                        chunks.append(name)
                elif isinstance(dependency, str) and dependency.strip():
                    chunks.append(dependency)
    return "\n".join(chunks)
