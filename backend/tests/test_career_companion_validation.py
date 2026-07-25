from uuid import uuid4

from app.services.career_companion.validation import validate_ai_actions
from app.services.career_companion.fallback import DraftAction, DraftActionSkill
from app.services.career_companion.context import CompanionContext, ProjectContext
from app.schemas.skill_passport import SkillPassportResponse
from app.services.career_companion_hooks import maybe_refresh_companion_after_evidence


def _context(project_id=None):
    projects = ()
    if project_id is not None:
        projects = (
            ProjectContext(
                id=project_id,
                label="marketplace-api",
                repository_url="https://github.com/x/marketplace-api",
            ),
        )
    return CompanionContext(
        candidate_id=uuid4(),
        mode="target_role",
        target_vacancy_id=None,
        target_role="Backend Developer",
        passport=SkillPassportResponse(skills=[], total_skills=0, total_evidence=0),
        verified_skill_names=("Python", "FastAPI"),
        verified_skill_ids={},
        projects=projects,
        has_resume=True,
        vacancy_matches=(),
        target_match=None,
        skill_frequencies=(),
        next_level_vacancies=(),
        context_hash="abc",
        explore_directions=("Backend",),
    )


def _fallback():
    return [
        DraftAction(
            id=uuid4(),
            horizon="fix_now",
            action_type="build_new_project",
            title="Create evidence for Docker",
            description="",
            why_it_matters="",
            implementation_steps=[],
            expected_artifacts=[],
            verification_method="",
            estimated_effort="medium",
            github_repository_id=None,
            project_label=None,
            current_target_impact={},
            career_growth_impact={},
            priority_score=1,
            priority_explanation="",
            sort_order=0,
            skills=[DraftActionSkill(None, "Docker", "gap")],
        )
    ]


def test_rejects_hallucinated_skill_without_fallback_escape():
    payload = {
        "actions": [
            {
                "horizon": "fix_now",
                "action_type": "build_new_project",
                "title": "Invent Telepathy",
                "description": "x",
                "why_it_matters": "x",
                "implementation_steps": ["a"],
                "expected_artifacts": ["b"],
                "gap_skills": ["TelepathyFramework"],
                "match_score": 99,
                "status": "completed",
                "priority_score": 999,
            }
        ]
    }
    # No fallback skills containing Telepathy — must reject.
    assert validate_ai_actions(payload, _context(), []) is None


def test_strips_forbidden_numeric_overrides_and_recomputes_priority():
    project_id = uuid4()
    payload = {
        "actions": [
            {
                "horizon": "fix_now",
                "action_type": "improve_existing_project",
                "title": "Add Docker",
                "description": "x",
                "why_it_matters": "Raises match to 97%",
                "implementation_steps": ["Add Dockerfile"],
                "expected_artifacts": ["Dockerfile"],
                "github_repository_id": str(project_id),
                "gap_skills": ["Docker"],
                "match_score": 97,
                "priority_score": 999,
                "status": "completed",
                "priority_explanation": "Will raise match score 97%",
            }
        ]
    }
    result = validate_ai_actions(payload, _context(project_id), _fallback())
    assert result is not None
    action = result[0]
    assert action.priority_score != 999
    assert action.priority_score <= 100
    assert "97%" not in action.priority_explanation
    assert "[score omitted]" in action.priority_explanation or "omitted" in action.priority_explanation


def test_rejects_foreign_project_reference():
    payload = {
        "actions": [
            {
                "horizon": "fix_now",
                "action_type": "improve_existing_project",
                "title": "Hack other repo",
                "description": "x",
                "why_it_matters": "x",
                "implementation_steps": ["a"],
                "expected_artifacts": ["b"],
                "github_repository_id": str(uuid4()),
                "gap_skills": ["Docker"],
            }
        ]
    }
    assert validate_ai_actions(payload, _context(uuid4()), _fallback()) is None


def test_refresh_hook_uses_isolated_session(monkeypatch):
    """Companion refresh must not use the caller session (no recursive ingest coupling)."""
    created = {"sessions": 0, "refreshed": 0}

    class FakeSession:
        def rollback(self):
            return None

        def close(self):
            return None

    def fake_session_local():
        created["sessions"] += 1
        return FakeSession()

    def fake_refresh(session, candidate_id):
        created["refreshed"] += 1
        assert isinstance(session, FakeSession)

    monkeypatch.setattr(
        "app.db.session.SessionLocal",
        fake_session_local,
    )
    monkeypatch.setattr(
        "app.services.career_companion.verification.refresh_plan_from_evidence",
        fake_refresh,
    )

    caller = object()
    maybe_refresh_companion_after_evidence(caller, uuid4())
    maybe_refresh_companion_after_evidence(caller, uuid4())
    assert created["sessions"] == 2
    assert created["refreshed"] == 2
