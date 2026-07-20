"""Deterministic Roadmap generation from an existing Skill Passport."""

from __future__ import annotations

from collections.abc import Sequence
from hashlib import sha256

from app.schemas.roadmap import RoadmapItemResponse, RoadmapResponse
from app.schemas.skill_passport import SkillPassportResponse
from app.utils.roadmap_rules import (
    ROADMAP_RULES,
    VACANCY_ROADMAP_TEMPLATES,
    RoadmapRule,
    priority_rank,
)
from app.utils.skill_name import InvalidSkillNameError, normalize_skill_name

MAX_CAREER_ROADMAP_ITEMS = 3


def build_roadmap_from_passport(passport: SkillPassportResponse) -> RoadmapResponse:
    """Derive roadmap items solely from Skill Passport skill names."""
    present_by_normalized: dict[str, str] = {}
    for skill in passport.skills:
        try:
            present_by_normalized[normalize_skill_name(skill.name)] = skill.name
        except InvalidSkillNameError:
            continue

    rules_by_target: dict[str, RoadmapRule] = {}
    for rule in ROADMAP_RULES:
        if not _matches(rule, present_by_normalized):
            continue
        for target in rule.missing_skills:
            normalized_target = _normalize_optional(target)
            if normalized_target is None:
                continue
            previous = rules_by_target.get(normalized_target)
            if previous is None or _career_rule_sort_key(rule) < _career_rule_sort_key(previous):
                rules_by_target[normalized_target] = rule

    selected_rules = sorted(rules_by_target.values(), key=_career_rule_sort_key)
    items = [_to_item(rule, present_by_normalized) for rule in selected_rules]
    return RoadmapResponse(items=items[:MAX_CAREER_ROADMAP_ITEMS])


def build_roadmap_from_match(
    required_missing: Sequence[str], preferred_missing: Sequence[str]
) -> RoadmapResponse:
    """Build a vacancy-specific roadmap from already-computed match gaps.

    Required gaps are emitted first at high priority; preferred gaps follow at
    medium priority. A normalized skill name can produce only one item, with
    the required occurrence taking precedence.
    """
    items: list[RoadmapItemResponse] = []
    seen: set[str] = set()
    for missing_skills, priority in (
        (required_missing, "high"),
        (preferred_missing, "medium"),
    ):
        for skill_name in missing_skills:
            normalized = _normalize_optional(skill_name)
            if normalized is None or normalized in seen:
                continue
            seen.add(normalized)
            items.append(_vacancy_gap_item(skill_name.strip(), normalized, priority))
    return RoadmapResponse(items=items)


def _matches(rule: RoadmapRule, present_by_normalized: dict[str, str]) -> bool:
    required = [_normalize_optional(name) for name in rule.required_skills]
    if any(name is None for name in required):
        return False
    if not all(name in present_by_normalized for name in required if name is not None):
        return False

    if rule.any_of_skills:
        any_of = [_normalize_optional(name) for name in rule.any_of_skills]
        if not any(name in present_by_normalized for name in any_of if name is not None):
            return False

    for absent in rule.absent_skills:
        normalized = _normalize_optional(absent)
        if normalized is not None and normalized in present_by_normalized:
            return False
    return True


def _career_rule_sort_key(rule: RoadmapRule) -> tuple[int, int, str]:
    """Prefer closer, more specific transitions with a stable tie-breaker."""
    specificity = len(rule.required_skills) + len(rule.any_of_skills)
    return (priority_rank(rule.priority), -specificity, rule.id)


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


def _vacancy_gap_item(
    skill_name: str, normalized_name: str, priority: str
) -> RoadmapItemResponse:
    template = VACANCY_ROADMAP_TEMPLATES.get(normalized_name)
    if template is not None:
        return RoadmapItemResponse(
            id=template.id,
            title=template.title,
            reason=template.reason,
            priority=priority,
            missing_skills=[skill_name],
            related_skills=[],
        )

    digest = sha256(normalized_name.encode("utf-8")).hexdigest()[:12]
    return RoadmapItemResponse(
        id=f"roadmap.vacancy_gap.generic_{digest}.v1",
        title=f"Learn {skill_name}",
        reason=(
            f"This vacancy requires {skill_name}. Build foundational knowledge and "
            f"complete a practical project demonstrating {skill_name}."
        ),
        priority=priority,
        missing_skills=[skill_name],
        related_skills=[],
    )


def _normalize_optional(value: str) -> str | None:
    try:
        return normalize_skill_name(value)
    except InvalidSkillNameError:
        return None
