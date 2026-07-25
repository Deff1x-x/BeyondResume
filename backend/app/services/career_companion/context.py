"""Deterministic profile context for AI Career Companion."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.github_repository import GitHubRepository
from app.models.resume import Resume
from app.models.skill import Skill
from app.services.candidate_vacancies import (
    CandidateVacancyMatch,
    list_candidate_vacancies,
)
from app.services.skill_passport import build_passport, empty_passport
from app.schemas.skill_passport import SkillPassportResponse


@dataclass(frozen=True, slots=True)
class ProjectContext:
    id: UUID
    label: str
    repository_url: str


@dataclass(frozen=True, slots=True)
class SkillFrequency:
    skill_id: UUID
    skill_name: str
    vacancy_count: int
    required_count: int
    preferred_count: int


@dataclass(frozen=True, slots=True)
class CompanionContext:
    candidate_id: UUID
    mode: str
    target_vacancy_id: UUID | None
    target_role: str | None
    passport: SkillPassportResponse
    verified_skill_names: tuple[str, ...]
    verified_skill_ids: dict[str, UUID]
    projects: tuple[ProjectContext, ...]
    has_resume: bool
    vacancy_matches: tuple[CandidateVacancyMatch, ...]
    target_match: CandidateVacancyMatch | None
    skill_frequencies: tuple[SkillFrequency, ...]
    next_level_vacancies: tuple[CandidateVacancyMatch, ...]
    context_hash: str
    explore_directions: tuple[str, ...] = field(default_factory=tuple)


def build_companion_context(
    session: Session,
    *,
    candidate_id: UUID,
    mode: str,
    target_vacancy_id: UUID | None = None,
    target_role: str | None = None,
) -> CompanionContext:
    passport = build_passport(session, candidate_id)
    if passport.total_skills == 0 and passport.total_evidence == 0:
        passport = empty_passport()

    verified_skill_ids: dict[str, UUID] = {}
    verified_names: list[str] = []
    for skill in passport.skills:
        key = skill.name.strip().lower()
        verified_skill_ids[key] = skill.id
        verified_names.append(skill.name)

    repos = session.execute(
        select(GitHubRepository).where(GitHubRepository.candidate_id == candidate_id)
    ).scalars().all()
    projects = tuple(
        ProjectContext(
            id=repo.id,
            label=_repo_label(repo.repository_url),
            repository_url=repo.repository_url,
        )
        for repo in repos
    )

    has_resume = (
        session.execute(
            select(Resume.id).where(Resume.candidate_id == candidate_id).limit(1)
        ).scalar_one_or_none()
        is not None
    )

    vacancy_matches = tuple(list_candidate_vacancies(session, candidate_id))
    target_match = None
    if mode == "target_vacancy" and target_vacancy_id is not None:
        target_match = next(
            (item for item in vacancy_matches if item.vacancy.id == target_vacancy_id),
            None,
        )

    role = (target_role or "").strip() or None
    if mode in {"target_role", "career_growth", "explore_direction"} and role is None:
        # Prefer profile target when caller omitted it.
        from app.models.candidate_profile import CandidateProfile

        profile = session.get(CandidateProfile, candidate_id)
        role = (profile.target_role if profile else None) or None

    skill_frequencies = _skill_frequencies(vacancy_matches, role)
    next_level = _next_level_vacancies(vacancy_matches, role, target_match)
    directions = _explore_directions(passport, vacancy_matches)

    payload = {
        "mode": mode,
        "target_vacancy_id": str(target_vacancy_id) if target_vacancy_id else None,
        "target_role": role,
        "skills": sorted(verified_names),
        "projects": sorted(p.repository_url for p in projects),
        "vacancy_ids": [str(item.vacancy.id) for item in vacancy_matches],
        "has_resume": has_resume,
    }
    context_hash = sha256(repr(sorted(payload.items())).encode("utf-8")).hexdigest()

    return CompanionContext(
        candidate_id=candidate_id,
        mode=mode,
        target_vacancy_id=target_vacancy_id,
        target_role=role,
        passport=passport,
        verified_skill_names=tuple(verified_names),
        verified_skill_ids=verified_skill_ids,
        projects=projects,
        has_resume=has_resume,
        vacancy_matches=vacancy_matches,
        target_match=target_match,
        skill_frequencies=skill_frequencies,
        next_level_vacancies=next_level,
        context_hash=context_hash,
        explore_directions=directions,
    )


def resolve_skill_id(session: Session, skill_name: str) -> UUID | None:
    normalized = skill_name.strip().lower()
    rows = session.execute(select(Skill).where(Skill.deprecated.is_(False))).scalars().all()
    for skill in rows:
        if skill.canonical_name.strip().lower() == normalized:
            return skill.id
        if skill.normalized_name.strip().lower() == normalized:
            return skill.id
    return None


def _repo_label(url: str) -> str:
    cleaned = url.rstrip("/")
    if "/" in cleaned:
        return cleaned.rsplit("/", 1)[-1]
    return cleaned


def _skill_frequencies(
    matches: tuple[CandidateVacancyMatch, ...], role: str | None
) -> tuple[SkillFrequency, ...]:
    relevant = matches
    if role:
        role_l = role.lower()
        filtered = tuple(
            item
            for item in matches
            if role_l in (item.vacancy.title or "").lower()
            or any(role_l in skill.lower() for skill in item.required_skills)
        )
        if filtered:
            relevant = filtered

    counts: dict[str, dict[str, object]] = {}
    for item in relevant:
        seen_names: set[str] = set()
        for skill_name, kind in (
            *((name, "required") for name in item.required_skills),
            *((name, "preferred") for name in item.preferred_skills),
        ):
            key = skill_name.strip().lower()
            if key in seen_names:
                continue
            seen_names.add(key)
            entry = counts.setdefault(
                key,
                {
                    "skill_name": skill_name,
                    "vacancy_count": 0,
                    "required_count": 0,
                    "preferred_count": 0,
                },
            )
            entry["vacancy_count"] = int(entry["vacancy_count"]) + 1
            if kind == "required":
                entry["required_count"] = int(entry["required_count"]) + 1
            else:
                entry["preferred_count"] = int(entry["preferred_count"]) + 1

    # skill_id filled later by caller if needed; use nil UUID placeholder via name only
    from uuid import uuid5, NAMESPACE_URL

    result = [
        SkillFrequency(
            skill_id=uuid5(NAMESPACE_URL, f"skill:{key}"),
            skill_name=str(data["skill_name"]),
            vacancy_count=int(data["vacancy_count"]),
            required_count=int(data["required_count"]),
            preferred_count=int(data["preferred_count"]),
        )
        for key, data in counts.items()
    ]
    result.sort(key=lambda item: (-item.required_count, -item.vacancy_count, item.skill_name))
    return tuple(result)


def _next_level_vacancies(
    matches: tuple[CandidateVacancyMatch, ...],
    role: str | None,
    target: CandidateVacancyMatch | None,
) -> tuple[CandidateVacancyMatch, ...]:
    role_l = (role or (target.vacancy.title if target else "") or "").lower()
    keywords = ("middle", "mid", "senior", "strong", "lead")
    junior_markers = ("junior", "jr", "intern", "entry")

    scored: list[tuple[int, CandidateVacancyMatch]] = []
    for item in matches:
        title = (item.vacancy.title or "").lower()
        if role_l and role_l.split()[0] not in title and not any(
            token in title for token in role_l.split() if len(token) > 3
        ):
            # Keep loosely related backend/frontend titles by shared tokens.
            if not any(token in title for token in ("backend", "frontend", "full", "devops", "data", "qa")):
                continue
        req_count = len(item.required_skills) + len(item.preferred_skills)
        boost = 0
        if any(k in title for k in keywords):
            boost += 3
        if target and req_count > (
            len(target.required_skills) + len(target.preferred_skills)
        ):
            boost += 2
        if any(k in title for k in junior_markers):
            boost -= 2
        if boost > 0 or req_count >= 6:
            scored.append((boost * 10 + req_count, item))

    scored.sort(key=lambda pair: -pair[0])
    return tuple(item for _, item in scored[:8])


def _explore_directions(
    passport: SkillPassportResponse, matches: tuple[CandidateVacancyMatch, ...]
) -> tuple[str, ...]:
    categories = [skill.category for skill in passport.skills]
    names = " ".join(skill.name.lower() for skill in passport.skills)
    scores = {
        "Backend": sum(1 for c in categories if "back" in c.lower()) + names.count("api") + names.count("python"),
        "Frontend": sum(1 for c in categories if "front" in c.lower()) + names.count("react") + names.count("css"),
        "DevOps": names.count("docker") + names.count("kubernetes") + names.count("ci"),
        "Data Engineering": names.count("sql") + names.count("spark") + names.count("etl"),
        "QA Automation": names.count("test") + names.count("selenium") + names.count("cypress"),
    }
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    return tuple(name for name, score in ranked if score > 0)[:4] or ("Backend",)
