"""Idempotent application-data seed for the baseline Skill ontology."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.skill import Skill
from app.models.skill_alias import SkillAlias
from app.utils.skill_name import normalize_skill_name

_ONTOLOGY_PATH = Path(__file__).parents[1] / "data" / "skill_ontology.json"


class SkillOntologySeedConflictError(RuntimeError):
    """Raised when the immutable seed name space conflicts with existing ontology data."""


@dataclass(frozen=True, slots=True)
class SkillOntologySeedDefinition:
    canonical_name: str
    category: str
    aliases: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SkillOntologySeedResult:
    skills_created: int
    skills_reused: int
    aliases_created: int
    aliases_reused: int


def load_skill_ontology_seed(path: Path = _ONTOLOGY_PATH) -> tuple[str, tuple[SkillOntologySeedDefinition, ...]]:
    """Load and validate the version-controlled baseline ontology."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Skill ontology seed must be an object")
    version = payload.get("version")
    raw_skills = payload.get("skills")
    if not isinstance(version, str) or not version.strip() or not isinstance(raw_skills, list):
        raise ValueError("Skill ontology seed has an invalid version or skills list")

    definitions: list[SkillOntologySeedDefinition] = []
    seen_canonical: set[str] = set()
    for raw_skill in raw_skills:
        if not isinstance(raw_skill, dict):
            raise ValueError("Skill ontology entries must be objects")
        canonical_name = raw_skill.get("canonical_name")
        category = raw_skill.get("category")
        aliases = raw_skill.get("aliases", [])
        if (
            not isinstance(canonical_name, str)
            or not isinstance(category, str)
            or not isinstance(aliases, list)
            or any(not isinstance(alias, str) for alias in aliases)
        ):
            raise ValueError("Skill ontology entry has invalid fields")
        normalized_canonical = normalize_skill_name(canonical_name)
        if normalized_canonical in seen_canonical:
            raise ValueError(f"Duplicate canonical skill in seed: {canonical_name}")
        seen_canonical.add(normalized_canonical)
        definitions.append(
            SkillOntologySeedDefinition(canonical_name, category, tuple(aliases))
        )
    return version.strip(), tuple(definitions)


def seed_skill_ontology(
    session: Session,
    *,
    version: str | None = None,
    definitions: tuple[SkillOntologySeedDefinition, ...] | None = None,
) -> SkillOntologySeedResult:
    """Add missing baseline Skills and aliases without changing existing ontology rows.

    The caller owns the transaction.  The CLI uses one ``Session.begin()`` block,
    so either the complete seed is committed or none of it is.
    """
    loaded_version, loaded_definitions = load_skill_ontology_seed()
    seed_version = version or loaded_version
    seed_definitions = definitions or loaded_definitions
    skills_created = skills_reused = aliases_created = aliases_reused = 0

    for definition in sorted(seed_definitions, key=lambda item: normalize_skill_name(item.canonical_name)):
        normalized_canonical = normalize_skill_name(definition.canonical_name)
        skill = session.execute(
            select(Skill).where(Skill.normalized_name == normalized_canonical)
        ).scalar_one_or_none()
        if skill is None:
            conflicting_alias = session.execute(
                select(SkillAlias).where(SkillAlias.normalized_alias == normalized_canonical)
            ).scalar_one_or_none()
            if conflicting_alias is not None:
                raise SkillOntologySeedConflictError(
                    f"Canonical skill conflicts with alias: {definition.canonical_name}"
                )
            skill = Skill(
                canonical_name=definition.canonical_name,
                normalized_name=normalized_canonical,
                category=definition.category,
                description=None,
                deprecated=False,
                ontology_version=seed_version,
            )
            session.add(skill)
            session.flush()
            skills_created += 1
        else:
            skills_reused += 1

        for alias in sorted(definition.aliases, key=normalize_skill_name):
            normalized_alias = normalize_skill_name(alias)
            if normalized_alias == skill.normalized_name:
                aliases_reused += 1
                continue
            existing_skill = session.execute(
                select(Skill).where(Skill.normalized_name == normalized_alias)
            ).scalar_one_or_none()
            if existing_skill is not None and existing_skill.id != skill.id:
                raise SkillOntologySeedConflictError(
                    f"Alias conflicts with canonical skill: {alias}"
                )
            existing_alias = session.execute(
                select(SkillAlias).where(SkillAlias.normalized_alias == normalized_alias)
            ).scalar_one_or_none()
            if existing_alias is None:
                session.add(SkillAlias(skill_id=skill.id, alias=alias, normalized_alias=normalized_alias))
                session.flush()
                aliases_created += 1
            elif existing_alias.skill_id == skill.id:
                aliases_reused += 1
            else:
                raise SkillOntologySeedConflictError(
                    f"Alias belongs to another skill: {alias}"
                )

    return SkillOntologySeedResult(
        skills_created=skills_created,
        skills_reused=skills_reused,
        aliases_created=aliases_created,
        aliases_reused=aliases_reused,
    )
