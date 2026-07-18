"""Read-only resolution of extracted GitHub skill candidates against the ontology."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sqlalchemy.orm import Session

from app.models.skill import Skill
from app.services.skill_ontology import resolve_skill
from app.utils.github_skill_extractor import GitHubSkillCandidate


@dataclass(frozen=True, slots=True)
class ResolvedGitHubSkillCandidate:
    """A persisted canonical Skill paired with its deterministic GitHub candidate."""

    skill: Skill
    candidate: GitHubSkillCandidate
    rule_id: str


def resolve_github_skill_candidates(
    session: Session,
    candidates: Iterable[GitHubSkillCandidate],
) -> tuple[ResolvedGitHubSkillCandidate, ...]:
    """Resolve unique target skill names only through the approved ontology resolver."""
    candidates_by_target: dict[str, GitHubSkillCandidate] = {}
    for candidate in candidates:
        existing = candidates_by_target.get(candidate.target_skill_name)
        if existing is None or _candidate_key(candidate) < _candidate_key(existing):
            candidates_by_target[candidate.target_skill_name] = candidate

    resolved: list[ResolvedGitHubSkillCandidate] = []
    for target_skill_name, candidate in sorted(candidates_by_target.items()):
        skill = resolve_skill(session, target_skill_name)
        if skill is not None:
            resolved.append(
                ResolvedGitHubSkillCandidate(
                    skill=skill,
                    candidate=candidate,
                    rule_id=candidate.rule_id,
                )
            )
    return tuple(resolved)


def _candidate_key(candidate: GitHubSkillCandidate) -> tuple[str, str, str, str, str, str]:
    return (
        candidate.target_skill_name,
        candidate.source_manifest,
        candidate.manifest_kind,
        candidate.ecosystem,
        candidate.source_dependency,
        candidate.signal_type,
    )
