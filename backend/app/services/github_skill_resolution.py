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
    """Resolve every source candidate only through the approved ontology resolver."""
    resolved: list[ResolvedGitHubSkillCandidate] = []
    for candidate in candidates:
        skill = resolve_skill(session, candidate.target_skill_name)
        if skill is not None:
            resolved.append(
                ResolvedGitHubSkillCandidate(
                    skill=skill,
                    candidate=candidate,
                    rule_id=candidate.rule_id,
                )
            )
    return tuple(sorted(resolved, key=_resolved_candidate_key))


def _resolved_candidate_key(
    resolved: ResolvedGitHubSkillCandidate,
) -> tuple[str, str, str, str, str, str, str, str]:
    candidate = resolved.candidate
    return (
        candidate.target_skill_name,
        candidate.signal_type,
        candidate.target_skill_name,
        candidate.source_manifest,
        candidate.manifest_kind,
        candidate.ecosystem,
        candidate.source_dependency,
        candidate.rule_id,
    )
