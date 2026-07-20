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
    # At least one of these skills must appear when the rule needs extra context.
    any_of_skills: tuple[str, ...] = ()

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
        if any(not skill.strip() for skill in self.any_of_skills):
            raise RoadmapRuleValidationError("Roadmap any_of_skills must be non-empty")


@dataclass(frozen=True, slots=True)
class VacancyRoadmapTemplate:
    """A deterministic recommendation template for a vacancy skill gap."""

    id: str
    title: str
    reason: str

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not _RULE_ID_PATTERN.fullmatch(self.id):
            raise RoadmapRuleValidationError("Vacancy roadmap template ID is invalid")
        if not self.title.strip() or not self.reason.strip():
            raise RoadmapRuleValidationError(
                "Vacancy roadmap template title and reason must be non-empty"
            )


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
            id="roadmap.react.from_frontend_foundations.v1",
            title="Build with React",
            reason=(
                "You have HTML, CSS, and JavaScript evidence. React is a natural next "
                "step for building structured interactive interfaces."
            ),
            priority="high",
            required_skills=("HTML", "CSS", "JavaScript"),
            absent_skills=("React",),
            missing_skills=("React",),
        ),
        RoadmapRule(
            id="roadmap.tailwind.from_css.v1",
            title="Add Tailwind CSS to your frontend toolkit",
            reason=(
                "You have CSS evidence. Tailwind CSS is a practical next tool for "
                "building consistent interfaces efficiently."
            ),
            priority="medium",
            required_skills=("CSS",),
            absent_skills=("Tailwind CSS",),
            missing_skills=("Tailwind CSS",),
        ),
        RoadmapRule(
            id="roadmap.fastapi.from_python.v1",
            title="Build an API with FastAPI",
            reason=(
                "You have Python evidence. FastAPI is a focused next step for building "
                "typed, production-oriented backend services."
            ),
            priority="high",
            required_skills=("Python",),
            absent_skills=("FastAPI",),
            missing_skills=("FastAPI",),
        ),
        RoadmapRule(
            id="roadmap.postgresql.from_fastapi.v1",
            title="Add PostgreSQL to your FastAPI stack",
            reason=(
                "You have FastAPI evidence. PostgreSQL is a practical next step for "
                "persistent application data and production backend work."
            ),
            priority="medium",
            required_skills=("FastAPI",),
            absent_skills=("PostgreSQL",),
            missing_skills=("PostgreSQL",),
        ),
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
            id="roadmap.typescript.from_javascript.v1",
            title="Add TypeScript to your JavaScript projects",
            reason=(
                "You have JavaScript evidence. TypeScript is a practical next step for "
                "safer interfaces and more maintainable application code."
            ),
            priority="medium",
            required_skills=("JavaScript",),
            absent_skills=("TypeScript",),
            missing_skills=("TypeScript",),
        ),
        RoadmapRule(
            id="roadmap.nextjs.from_react_typescript.v1",
            title="Build with Next.js",
            reason=(
                "You have React and TypeScript evidence. Next.js is a focused next step "
                "for full-stack React applications and production delivery."
            ),
            priority="high",
            required_skills=("React", "TypeScript"),
            absent_skills=("Next.js",),
            missing_skills=("Next.js",),
        ),
        RoadmapRule(
            id="roadmap.testing.from_node_javascript.v1",
            title="Add automated testing to your Node.js projects",
            reason=(
                "You have Node.js and JavaScript evidence. Add automated tests to make "
                "your backend or tooling work more reliable."
            ),
            priority="medium",
            required_skills=("Node.js", "JavaScript"),
            absent_skills=("Testing", "Jest"),
            missing_skills=("Testing",),
        ),
        RoadmapRule(
            id="roadmap.testing.from_node.v1",
            title="Add automated testing for Node.js",
            reason=(
                "You have Node.js evidence. Automated tests are a practical next step "
                "for reliable services and tooling."
            ),
            priority="medium",
            required_skills=("Node.js",),
            absent_skills=("Testing", "Jest"),
            missing_skills=("Testing",),
        ),
        RoadmapRule(
            id="roadmap.cicd.from_docker.v1",
            title="Set up CI/CD for your containerized work",
            reason=(
                "You have Docker evidence. Automating checks and delivery is the next "
                "engineering practice for a repeatable deployment workflow."
            ),
            priority="low",
            required_skills=("Docker",),
            absent_skills=("GitHub Actions", "CI/CD"),
            missing_skills=("CI/CD",),
        ),
        RoadmapRule(
            id="roadmap.kubernetes.from_backend_docker.v1",
            title="Learn Kubernetes for backend workloads",
            reason=(
                "You have FastAPI and Docker evidence. Kubernetes is a relevant next "
                "step for deploying and operating backend services."
            ),
            priority="low",
            required_skills=("FastAPI", "Docker"),
            absent_skills=("Kubernetes",),
            missing_skills=("Kubernetes",),
        ),
        RoadmapRule(
            id="roadmap.redis.from_backend_postgresql.v1",
            title="Add Redis to your backend stack",
            reason=(
                "You have FastAPI and PostgreSQL evidence. Redis is a useful next step "
                "for caching and lightweight data-access patterns."
            ),
            priority="low",
            required_skills=("FastAPI", "PostgreSQL"),
            absent_skills=("Redis",),
            missing_skills=("Redis",),
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


# Keys are normalized skill names; normalization itself remains centralized in
# ``app.utils.skill_name`` and is applied by the roadmap service.
VACANCY_ROADMAP_TEMPLATES: Final[dict[str, VacancyRoadmapTemplate]] = {
    "c#": VacancyRoadmapTemplate(
        id="roadmap.vacancy_gap.csharp.v1",
        title="Build C# fundamentals",
        reason="This vacancy requires C#. Build practical experience with the language and its core tooling.",
    ),
    "redis": VacancyRoadmapTemplate(
        id="roadmap.vacancy_gap.redis.v1",
        title="Learn Redis",
        reason="This vacancy requires Redis. Practice caching and data-access patterns in a working service.",
    ),
    "kubernetes": VacancyRoadmapTemplate(
        id="roadmap.vacancy_gap.kubernetes.v1",
        title="Learn Kubernetes",
        reason="This vacancy requires Kubernetes. Practice deploying and operating a small application workload.",
    ),
}
