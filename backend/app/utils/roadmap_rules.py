"""Deterministic roadmap recommendation rules.

Rules are data, not endpoint logic. Add new recommendations by appending to
``ROADMAP_RULES`` — matching stays in ``app.services.roadmap``.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Final, Literal

RoadmapPriority = Literal["high", "medium", "low"]

_RULE_ID_PATTERN: Final = re.compile(r"^roadmap\.[a-z0-9_]+(?:\.[a-z0-9_]+)+\.v[1-9][0-9]*$")
_PRIORITY_RANK: Final[dict[RoadmapPriority, int]] = {"high": 0, "medium": 1, "low": 2}


class RoadmapRuleValidationError(ValueError):
    """Raised when the static roadmap rule registry is invalid."""


@dataclass(frozen=True, slots=True)
class RoadmapRule:
    """One deterministic gap-filling recommendation over Skill Passport skills."""

    id: str
    title: str
    reason: str
    priority: RoadmapPriority
    # All of these must already appear in the passport.
    required_skills: tuple[str, ...]
    # All of these must be absent; if any is present the rule does not fire.
    absent_skills: tuple[str, ...]
    # Skills the candidate is advised to acquire (shown as missing_skills).
    missing_skills: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not _RULE_ID_PATTERN.fullmatch(self.id):
            raise RoadmapRuleValidationError("Roadmap rule ID is invalid")
        if self.priority not in _PRIORITY_RANK:
            raise RoadmapRuleValidationError("Roadmap rule priority is invalid")
        if not self.title.strip() or not self.reason.strip():
            raise RoadmapRuleValidationError("Roadmap rule title and reason must be non-empty")
        if not self.required_skills:
            raise RoadmapRuleValidationError("Roadmap rule requires at least one required skill")
        if not self.absent_skills or not self.missing_skills:
            raise RoadmapRuleValidationError(
                "Roadmap rule requires absent_skills and missing_skills"
            )
        if any(not skill.strip() for skill in self.required_skills):
            raise RoadmapRuleValidationError("Roadmap required_skills must be non-empty")
        if any(not skill.strip() for skill in (*self.absent_skills, *self.missing_skills)):
            raise RoadmapRuleValidationError("Roadmap skill names must be non-empty")


def validate_roadmap_rules(rules: tuple[RoadmapRule, ...]) -> tuple[RoadmapRule, ...]:
    """Fail fast on duplicate IDs; return rules in declaration order."""
    seen: set[str] = set()
    for rule in rules:
        if rule.id in seen:
            raise RoadmapRuleValidationError(f"Duplicate roadmap rule ID: {rule.id}")
        seen.add(rule.id)
    return rules


def priority_rank(priority: RoadmapPriority) -> int:
    return _PRIORITY_RANK[priority]


ROADMAP_RULES: Final[tuple[RoadmapRule, ...]] = validate_roadmap_rules(
    (
        RoadmapRule(
            id="roadmap.docker.from_fastapi_postgresql.v1",
            title="Add Docker to your stack",
            reason=(
                "You already have FastAPI and PostgreSQL evidence. Learning Docker "
                "is the natural next step for packaging and running that stack reliably."
            ),
            priority="high",
            required_skills=("FastAPI", "PostgreSQL"),
            absent_skills=("Docker",),
            missing_skills=("Docker",),
        ),
        RoadmapRule(
            id="roadmap.testing.from_python.v1",
            title="Add automated testing for Python",
            reason=(
                "Python is present in your passport, but there is no Testing evidence yet. "
                "Automated tests make your Python work more credible to employers."
            ),
            priority="high",
            required_skills=("Python",),
            absent_skills=("Testing", "Pytest"),
            missing_skills=("Testing",),
        ),
        RoadmapRule(
            id="roadmap.typescript.from_react.v1",
            title="Adopt TypeScript with React",
            reason=(
                "You have React evidence without TypeScript. Adding TypeScript strengthens "
                "frontend type safety and is expected in many React roles."
            ),
            priority="medium",
            required_skills=("React",),
            absent_skills=("TypeScript",),
            missing_skills=("TypeScript",),
        ),
        RoadmapRule(
            id="roadmap.cicd.from_git.v1",
            title="Set up CI/CD",
            reason=(
                "You have Git evidence, but no GitHub Actions or CI/CD signal yet. "
                "Automating checks and delivery is a common next step after version control."
            ),
            priority="medium",
            required_skills=("Git",),
            absent_skills=("GitHub Actions", "CI/CD"),
            missing_skills=("CI/CD",),
        ),
    )
)
