from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.skill import Skill
from app.models.skill_alias import SkillAlias
from app.utils.skill_name import normalize_skill_name


class OntologyNameCollisionError(Exception):
    """Raised when a Skill or SkillAlias collides in the shared name space."""


class SkillNotFoundError(Exception):
    """Raised when an alias references an unknown Skill."""


def create_skill(
    session: Session,
    *,
    canonical_name: str,
    category: str,
    description: str | None,
    ontology_version: str,
    deprecated: bool = False,
) -> Skill:
    normalized_name = normalize_skill_name(canonical_name)
    _ensure_name_is_available(session, normalized_name)
    skill = Skill(
        canonical_name=canonical_name,
        normalized_name=normalized_name,
        category=category,
        description=description,
        ontology_version=ontology_version,
        deprecated=deprecated,
    )
    session.add(skill)
    session.flush()
    return skill


def create_skill_alias(session: Session, *, skill_id: UUID, alias: str) -> SkillAlias:
    skill = session.execute(select(Skill).where(Skill.id == skill_id)).scalar_one_or_none()
    if skill is None:
        raise SkillNotFoundError
    normalized_alias = normalize_skill_name(alias)
    _ensure_name_is_available(session, normalized_alias)
    skill_alias = SkillAlias(
        skill_id=skill.id,
        alias=alias,
        normalized_alias=normalized_alias,
    )
    session.add(skill_alias)
    session.flush()
    return skill_alias


def resolve_skill(session: Session, skill_name: str) -> Skill | None:
    normalized_name = normalize_skill_name(skill_name)
    skill = session.execute(
        select(Skill).where(Skill.normalized_name == normalized_name)
    ).scalar_one_or_none()
    if skill is not None:
        return skill
    return session.execute(
        select(Skill).join(SkillAlias).where(SkillAlias.normalized_alias == normalized_name)
    ).scalar_one_or_none()


def _ensure_name_is_available(session: Session, normalized_name: str) -> None:
    skill = session.execute(
        select(Skill.id).where(Skill.normalized_name == normalized_name)
    ).scalar_one_or_none()
    if skill is not None:
        raise OntologyNameCollisionError
    alias = session.execute(
        select(SkillAlias.id).where(SkillAlias.normalized_alias == normalized_name)
    ).scalar_one_or_none()
    if alias is not None:
        raise OntologyNameCollisionError
