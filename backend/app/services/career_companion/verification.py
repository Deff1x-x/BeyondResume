"""Evidence re-check for active Career Companion actions."""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.career_companion_plan import CareerCompanionPlan
from app.models.career_companion_progress_event import CareerCompanionProgressEvent
from app.models.evidence_unit import EvidenceUnit
from app.models.vacancy import Vacancy
from app.models.vacancy_skill_requirement import VacancySkillRequirement
from app.services.career_companion.plan_service import get_active_plan
from app.services.matching import MatchRequirement, match_passport_to_requirements
from app.services.skill_passport import build_passport


ACTIVE_STATUSES = {
    "accepted",
    "in_progress",
    "awaiting_evidence",
    "evidence_detected",
    "partially_verified",
}


def refresh_plan_from_evidence(session: Session, candidate_id: UUID) -> CareerCompanionPlan | None:
    plan = get_active_plan(session, candidate_id)
    if plan is None:
        return None

    passport = build_passport(session, candidate_id)
    verified = {skill.name.strip().lower() for skill in passport.skills}
    evidence_rows = session.execute(
        select(EvidenceUnit).where(EvidenceUnit.candidate_id == candidate_id)
    ).scalars().all()
    corpus = " ".join(
        f"{row.title or ''} {row.description or ''} {row.source_reference or ''}".lower()
        for row in evidence_rows
    )

    previous_match = None
    if isinstance(plan.summary, dict):
        previous_match = plan.summary.get("last_match_score")

    changed = False
    for action in plan.actions:
        if action.status not in ACTIVE_STATUSES and action.status != "suggested":
            continue

        gap_names = [
            link.skill_name.strip().lower()
            for link in action.skills
            if link.role in {"gap", "potential_cover"}
        ]
        if not gap_names:
            continue

        covered = [name for name in gap_names if name in verified or name in corpus]
        artifacts_hit = [
            artifact
            for artifact in action.expected_artifacts
            if str(artifact).lower().split(".")[0] in corpus
            or str(artifact).lower() in corpus
        ]

        previous = action.status
        if covered and len(covered) >= len(gap_names) and (
            not action.expected_artifacts or artifacts_hit
        ):
            action.status = "completed"
        elif covered and len(covered) < len(gap_names):
            action.status = "partially_verified"
        elif artifacts_hit or covered:
            action.status = "evidence_detected"
        elif action.status in {"accepted", "in_progress"}:
            action.status = "awaiting_evidence"

        if action.status != previous:
            changed = True
            session.add(
                CareerCompanionProgressEvent(
                    id=uuid4(),
                    plan_id=plan.id,
                    event_type="evidence_progress",
                    title="Progress detected",
                    detail=(
                        f"{action.title}: {action.status.replace('_', ' ')}. "
                        f"Covered signals: {', '.join(covered) or 'none yet'}."
                    ),
                    payload={
                        "action_id": str(action.id),
                        "status": action.status,
                        "covered_skills": covered,
                        "artifacts_hit": artifacts_hit,
                    },
                )
            )

    match_score = _target_match_score(session, plan, passport)
    if match_score is not None:
        summary = dict(plan.summary or {})
        summary["last_match_score"] = match_score
        plan.summary = summary
        position = dict(plan.current_position or {})
        position["target_match_score"] = match_score
        plan.current_position = position
        if previous_match is not None and int(previous_match) != int(match_score):
            delta = int(match_score) - int(previous_match)
            direction = "up" if delta > 0 else "down"
            session.add(
                CareerCompanionProgressEvent(
                    id=uuid4(),
                    plan_id=plan.id,
                    event_type="match_delta",
                    title=f"Match score moved {direction}",
                    detail=(
                        f"Target match changed from {previous_match}% to {match_score}% "
                        f"({delta:+d} pts) after evidence refresh."
                    ),
                    payload={
                        "previous": previous_match,
                        "current": match_score,
                        "delta": delta,
                    },
                )
            )
            changed = True
        elif previous_match is None:
            changed = True

    if changed:
        session.commit()
    return get_active_plan(session, candidate_id)


def _target_match_score(session: Session, plan: CareerCompanionPlan, passport) -> int | None:
    if plan.target_vacancy_id is None:
        return None
    vacancy = session.execute(
        select(Vacancy)
        .where(Vacancy.id == plan.target_vacancy_id)
        .options(
            selectinload(Vacancy.skill_requirements).selectinload(VacancySkillRequirement.skill)
        )
    ).scalar_one_or_none()
    if vacancy is None:
        return None
    requirements: list[MatchRequirement] = []
    for req in vacancy.skill_requirements or []:
        skill_name = getattr(getattr(req, "skill", None), "canonical_name", None) or str(
            req.skill_id
        )
        requirements.append(
            MatchRequirement(
                skill_id=req.skill_id,
                skill_name=skill_name,
                requirement_type=req.requirement_type,
            )
        )
    if not requirements:
        return None
    result = match_passport_to_requirements(passport, requirements)
    return int(result.score)
