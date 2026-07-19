from uuid import UUID, uuid4

from app.schemas.skill_passport import SkillPassportResponse, SkillPassportSkillResponse
from app.services.matching import (
    PREFERRED_WEIGHT,
    REQUIRED_WEIGHT,
    MatchRequirement,
    match_passport_to_requirements,
)


def _passport_with_ids(skills: list[tuple[UUID, str]]) -> SkillPassportResponse:
    items = [
        SkillPassportSkillResponse(
            id=skill_id,
            name=name,
            category="general",
            evidence_confidence=1.0,
            evidence_count=1,
            evidence=[],
        )
        for skill_id, name in skills
    ]
    return SkillPassportResponse(
        skills=items, total_skills=len(items), total_evidence=len(items)
    )


def test_weights_are_split_seventy_thirty() -> None:
    assert REQUIRED_WEIGHT == 70
    assert PREFERRED_WEIGHT == 30
    assert REQUIRED_WEIGHT + PREFERRED_WEIGHT == 100


def test_full_match_scores_one_hundred() -> None:
    python_id, docker_id, react_id = uuid4(), uuid4(), uuid4()
    passport = _passport_with_ids(
        [(python_id, "Python"), (docker_id, "Docker"), (react_id, "React")]
    )
    requirements = [
        MatchRequirement(python_id, "Python", "required"),
        MatchRequirement(docker_id, "Docker", "required"),
        MatchRequirement(react_id, "React", "preferred"),
    ]

    result = match_passport_to_requirements(passport, requirements)

    assert result.score == 100
    assert result.required.matched == ("Python", "Docker")
    assert result.required.missing == ()
    assert result.preferred.matched == ("React",)
    assert result.preferred.missing == ()


def test_missing_required_lowers_score_more_than_missing_preferred() -> None:
    python_id, docker_id, react_id, ts_id = uuid4(), uuid4(), uuid4(), uuid4()
    passport = _passport_with_ids([(python_id, "Python"), (react_id, "React")])
    requirements = [
        MatchRequirement(python_id, "Python", "required"),
        MatchRequirement(docker_id, "Docker", "required"),
        MatchRequirement(react_id, "React", "preferred"),
        MatchRequirement(ts_id, "TypeScript", "preferred"),
    ]

    result = match_passport_to_requirements(passport, requirements)

    # required 1/2 * 70 + preferred 1/2 * 30 = 35 + 15 = 50
    assert result.score == 50
    assert result.required.matched == ("Python",)
    assert result.required.missing == ("Docker",)
    assert result.preferred.matched == ("React",)
    assert result.preferred.missing == ("TypeScript",)


def test_only_required_uses_full_scale() -> None:
    python_id, docker_id = uuid4(), uuid4()
    passport = _passport_with_ids([(python_id, "Python")])
    requirements = [
        MatchRequirement(python_id, "Python", "required"),
        MatchRequirement(docker_id, "Docker", "required"),
    ]

    result = match_passport_to_requirements(passport, requirements)

    assert result.score == 50
    assert result.preferred.matched == ()
    assert result.preferred.missing == ()


def test_only_preferred_uses_full_scale() -> None:
    react_id, ts_id = uuid4(), uuid4()
    passport = _passport_with_ids([(react_id, "React")])
    requirements = [
        MatchRequirement(react_id, "React", "preferred"),
        MatchRequirement(ts_id, "TypeScript", "preferred"),
    ]

    result = match_passport_to_requirements(passport, requirements)
    assert result.score == 50


def test_empty_requirements_score_zero() -> None:
    passport = _passport_with_ids([(uuid4(), "Python")])
    result = match_passport_to_requirements(passport, [])
    assert result.score == 0


def test_empty_passport_against_requirements() -> None:
    skill_id = uuid4()
    result = match_passport_to_requirements(
        SkillPassportResponse(skills=[], total_skills=0, total_evidence=0),
        [MatchRequirement(skill_id, "Python", "required")],
    )
    assert result.score == 0
    assert result.required.missing == ("Python",)
    assert result.required.matched == ()
