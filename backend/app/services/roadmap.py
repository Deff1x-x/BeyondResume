"""Deterministic Roadmap generation from an existing Skill Passport."""

from __future__ import annotations

from app.schemas.roadmap import RoadmapItemResponse, RoadmapResponse
from app.schemas.skill_passport import SkillPassportResponse
from app.utils.roadmap_rules import ROADMAP_RULES, RoadmapRule, priority_rank
from app.utils.skill_name import InvalidSkillNameError, normalize_skill_name


def build_roadmap_from_passport(passport: SkillPassportResponse) -> RoadmapResponse:
    """Derive roadmap items solely from Skill Passport skill names."""
    present_by_normalized: dict[str, str] = {}
    for skill in passport.skills:
        try:
            present_by_normalized[normalize_skill_name(skill.name)] = skill.name
        except InvalidSkillNameError:
            continue

    items = [
        _to_item(rule, present_by_normalized)
        for rule in ROADMAP_RULES
        if _matches(rule, present_by_normalized)
    ]
    items.sort(key=lambda item: (priority_rank(item.priority), item.id))
    return RoadmapResponse(items=items)


def _matches(rule: RoadmapRule, present_by_normalized: dict[str, str]) -> bool:
    required = [_normalize_optional(name) for name in rule.required_skills]
    if any(name is None for name in required):
        return False
    if not all(name in present_by_normalized for name in required if name is not None):
        return False

    for absent in rule.absent_skills:
        normalized = _normalize_optional(absent)
        if normalized is not None and normalized in present_by_normalized:
            return False
    return True


def _to_item(
    rule: RoadmapRule, present_by_normalized: dict[str, str]
) -> RoadmapItemResponse:
    related: list[str] = []
    for required in rule.required_skills:
        normalized = _normalize_optional(required)
        if normalized is None:
            continue
        related.append(present_by_normalized.get(normalized, required))
    return RoadmapItemResponse(
        id=rule.id,
        title=rule.title,
        reason=rule.reason,
        priority=rule.priority,
        missing_skills=list(rule.missing_skills),
        related_skills=related,
    )


def _normalize_optional(value: str) -> str | None:
    try:
        return normalize_skill_name(value)
    except InvalidSkillNameError:
        return None
