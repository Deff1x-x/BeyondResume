from uuid import uuid4

import pytest

from app.schemas.skill_passport import SkillPassportResponse, SkillPassportSkillResponse
from app.services.roadmap import build_roadmap_from_passport
from app.utils.roadmap_rules import (
    ROADMAP_RULES,
    RoadmapRule,
    RoadmapRuleValidationError,
    validate_roadmap_rules,
)


def _passport(*names: str) -> SkillPassportResponse:
    skills = [
        SkillPassportSkillResponse(
            id=uuid4(),
            name=name,
            category="general",
            evidence_confidence=1.0,
            evidence_count=1,
            evidence=[],
        )
        for name in names
    ]
    return SkillPassportResponse(
        skills=skills, total_skills=len(skills), total_evidence=len(skills)
    )


def test_registry_contains_example_rules() -> None:
    ids = {rule.id for rule in ROADMAP_RULES}
    assert "roadmap.docker.from_fastapi_postgresql.v1" in ids
    assert "roadmap.testing.from_python.v1" in ids
    assert "roadmap.typescript.from_react.v1" in ids
    assert "roadmap.cicd.from_git.v1" in ids


def test_validate_roadmap_rules_rejects_duplicate_ids() -> None:
    rule = ROADMAP_RULES[0]
    with pytest.raises(RoadmapRuleValidationError, match="Duplicate"):
        validate_roadmap_rules((rule, rule))


def test_validate_roadmap_rules_rejects_invalid_id() -> None:
    with pytest.raises(RoadmapRuleValidationError):
        RoadmapRule(
            id="bad-id",
            title="Title",
            reason="Reason",
            priority="high",
            required_skills=("Python",),
            absent_skills=("Testing",),
            missing_skills=("Testing",),
        )


def test_docker_rule_requires_fastapi_and_postgresql() -> None:
    matched = build_roadmap_from_passport(_passport("FastAPI", "PostgreSQL"))
    assert any(item.id == "roadmap.docker.from_fastapi_postgresql.v1" for item in matched.items)

    blocked = build_roadmap_from_passport(_passport("FastAPI", "PostgreSQL", "Docker"))
    assert all(item.id != "roadmap.docker.from_fastapi_postgresql.v1" for item in blocked.items)

    incomplete = build_roadmap_from_passport(_passport("FastAPI"))
    assert all(
        item.id != "roadmap.docker.from_fastapi_postgresql.v1" for item in incomplete.items
    )


def test_python_testing_rule() -> None:
    matched = build_roadmap_from_passport(_passport("Python"))
    item = next(i for i in matched.items if i.id == "roadmap.testing.from_python.v1")
    assert item.missing_skills == ["Testing"]
    assert item.related_skills == ["Python"]
    assert item.priority == "high"

    blocked_by_pytest = build_roadmap_from_passport(_passport("Python", "Pytest"))
    assert all(i.id != "roadmap.testing.from_python.v1" for i in blocked_by_pytest.items)


def test_react_typescript_and_git_cicd_rules() -> None:
    matched = build_roadmap_from_passport(_passport("React", "Git"))
    ids = [item.id for item in matched.items]
    assert "roadmap.typescript.from_react.v1" in ids
    assert "roadmap.cicd.from_git.v1" in ids

    typescript_item = next(i for i in matched.items if i.id == "roadmap.typescript.from_react.v1")
    assert typescript_item.missing_skills == ["TypeScript"]

    cicd_item = next(i for i in matched.items if i.id == "roadmap.cicd.from_git.v1")
    assert cicd_item.missing_skills == ["CI/CD"]

    blocked = build_roadmap_from_passport(_passport("React", "TypeScript", "Git", "GitHub Actions"))
    blocked_ids = {item.id for item in blocked.items}
    assert "roadmap.typescript.from_react.v1" not in blocked_ids
    assert "roadmap.cicd.from_git.v1" not in blocked_ids


def test_matching_is_case_insensitive_and_sorted_by_priority() -> None:
    matched = build_roadmap_from_passport(_passport("python", "react", "git"))
    ids = [item.id for item in matched.items]
    assert ids.index("roadmap.testing.from_python.v1") < ids.index(
        "roadmap.typescript.from_react.v1"
    )
    assert ids.index("roadmap.testing.from_python.v1") < ids.index("roadmap.cicd.from_git.v1")


def test_empty_passport_yields_empty_roadmap() -> None:
    assert build_roadmap_from_passport(_passport()).items == []
