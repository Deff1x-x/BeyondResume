from uuid import uuid4

import pytest

from app.schemas.skill_passport import SkillPassportResponse, SkillPassportSkillResponse
from app.services.roadmap import build_roadmap_from_match, build_roadmap_from_passport
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
    matched = build_roadmap_from_passport(_passport("python", "react"))
    ids = [item.id for item in matched.items]
    assert ids.index("roadmap.testing.from_python.v1") < ids.index(
        "roadmap.typescript.from_react.v1"
    )


def test_empty_passport_yields_empty_roadmap() -> None:
    assert build_roadmap_from_passport(_passport()).items == []


def test_frontend_foundations_recommend_react_without_recommending_present_skills() -> None:
    roadmap = build_roadmap_from_passport(
        _passport("CSS", "HTML", "JavaScript", "TypeScript")
    )

    recommended = [skill for item in roadmap.items for skill in item.missing_skills]
    assert "React" in recommended
    assert not {"CSS", "HTML", "JavaScript", "TypeScript"}.intersection(recommended)


def test_css_without_tailwind_recommends_tailwind() -> None:
    roadmap = build_roadmap_from_passport(_passport("CSS"))

    assert any(item.missing_skills == ["Tailwind CSS"] for item in roadmap.items)


def test_javascript_without_typescript_recommends_typescript() -> None:
    roadmap = build_roadmap_from_passport(_passport("JavaScript"))

    assert any(item.missing_skills == ["TypeScript"] for item in roadmap.items)


def test_react_and_typescript_recommend_nextjs() -> None:
    roadmap = build_roadmap_from_passport(_passport("React", "TypeScript"))

    assert any(item.missing_skills == ["Next.js"] for item in roadmap.items)


def test_python_recommends_fastapi_and_testing() -> None:
    roadmap = build_roadmap_from_passport(_passport("Python"))

    recommended = [skill for item in roadmap.items for skill in item.missing_skills]
    assert "FastAPI" in recommended
    assert "Testing" in recommended


def test_present_target_blocks_its_career_recommendation() -> None:
    roadmap = build_roadmap_from_passport(_passport("CSS", "Tailwind CSS"))

    assert all(item.missing_skills != ["Tailwind CSS"] for item in roadmap.items)


def test_more_specific_rule_wins_when_rules_share_a_target() -> None:
    roadmap = build_roadmap_from_passport(_passport("Node.js", "JavaScript"))

    testing = next(item for item in roadmap.items if item.missing_skills == ["Testing"])
    assert testing.id == "roadmap.testing.from_node_javascript.v1"


def test_career_roadmap_is_capped() -> None:
    roadmap = build_roadmap_from_passport(
        _passport(
            "HTML", "CSS", "JavaScript", "Python", "FastAPI", "PostgreSQL", "Docker", "Git"
        )
    )

    assert len(roadmap.items) == 3


def test_vacancy_roadmap_required_csharp_gap_uses_specialized_high_priority_item() -> None:
    roadmap = build_roadmap_from_match(required_missing=["C#"], preferred_missing=[])

    assert len(roadmap.items) == 1
    item = roadmap.items[0]
    assert item.id == "roadmap.vacancy_gap.csharp.v1"
    assert item.priority == "high"
    assert item.missing_skills == ["C#"]


def test_vacancy_roadmap_orders_required_before_preferred() -> None:
    roadmap = build_roadmap_from_match(
        required_missing=["C#"], preferred_missing=["Redis"]
    )

    assert [item.missing_skills for item in roadmap.items] == [["C#"], ["Redis"]]
    assert [item.priority for item in roadmap.items] == ["high", "medium"]


def test_vacancy_roadmap_deduplicates_required_and_preferred_by_normalized_name() -> None:
    roadmap = build_roadmap_from_match(
        required_missing=[" C# "], preferred_missing=["c#"]
    )

    assert len(roadmap.items) == 1
    assert roadmap.items[0].priority == "high"
    assert roadmap.items[0].missing_skills == ["C#"]


def test_vacancy_roadmap_unknown_skill_uses_generic_fallback() -> None:
    roadmap = build_roadmap_from_match(
        required_missing=["Elixir"], preferred_missing=[]
    )

    assert len(roadmap.items) == 1
    item = roadmap.items[0]
    assert item.id.startswith("roadmap.vacancy_gap.generic_")
    assert item.title == "Learn Elixir"
    assert item.priority == "high"
    assert item.missing_skills == ["Elixir"]


def test_vacancy_roadmap_without_missing_skills_is_empty() -> None:
    assert build_roadmap_from_match(required_missing=[], preferred_missing=[]).items == []
