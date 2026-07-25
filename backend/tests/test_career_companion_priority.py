from app.services.career_companion.priority import score_action
from app.services.career_companion.gaps import SkillGap


def test_required_gaps_outrank_preferred_only():
    required = [
        SkillGap("Docker", None, "required", 3, 3, 0, "not_found"),
        SkillGap("Testing", None, "required", 2, 2, 0, "not_found"),
    ]
    preferred = [SkillGap("Redis", None, "preferred", 4, 0, 4, "not_found")]
    high = score_action(
        gaps_covered=required, uses_existing_project=True, horizon="fix_now"
    )
    low = score_action(
        gaps_covered=preferred, uses_existing_project=False, horizon="build_next"
    )
    assert high.score > low.score
    assert "required" in high.explanation.lower()


def test_existing_project_bonus():
    gaps = [SkillGap("Docker", None, "required", 2, 2, 0, "not_found")]
    with_project = score_action(
        gaps_covered=gaps, uses_existing_project=True, horizon="fix_now"
    )
    without = score_action(
        gaps_covered=gaps, uses_existing_project=False, horizon="fix_now"
    )
    assert with_project.score > without.score
