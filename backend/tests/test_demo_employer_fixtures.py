"""Demo Mode employer fixture realism: scores, applicants, isolation."""

from __future__ import annotations

from collections.abc import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.models.user import User
from app.services.demo_users import (
    DEMO_CANDIDATE_EMAILS,
    DEMO_EMPLOYER_EMAIL,
    is_demo_email,
)
from app.services.matching import MatchRequirement, match_passport_to_requirements
from app.schemas.skill_passport import (
    SkillPassportResponse,
    SkillPassportSkillResponse,
)


def test_demo_platform_fixture_scores_are_realistic_and_distinct() -> None:
    """Mirror Senior Platform Engineer demo requirements (fixture contract)."""
    # Skill IDs only need to be stable within this test.
    ids = {name: uuid4() for name in (
        "Python",
        "PostgreSQL",
        "Docker",
        "FastAPI",
        "TypeScript",
        "React",
        "Kubernetes",
        "Redis",
    )}
    requirements = [
        MatchRequirement(ids["Python"], "Python", "required"),
        MatchRequirement(ids["PostgreSQL"], "PostgreSQL", "required"),
        MatchRequirement(ids["Docker"], "Docker", "required"),
        MatchRequirement(ids["FastAPI"], "FastAPI", "required"),
        MatchRequirement(ids["TypeScript"], "TypeScript", "preferred"),
        MatchRequirement(ids["React"], "React", "preferred"),
        MatchRequirement(ids["Kubernetes"], "Kubernetes", "preferred"),
        MatchRequirement(ids["Redis"], "Redis", "preferred"),
    ]

    profiles = {
        "Alex Rivera": ("Python", "PostgreSQL", "Docker", "FastAPI", "TypeScript", "Redis"),
        "Jordan Lee": ("Python", "PostgreSQL", "FastAPI", "TypeScript", "React", "Redis"),
        "Sam Okonkwo": ("Python", "PostgreSQL", "TypeScript", "React", "Redis", "Kubernetes"),
        "Casey Nguyen": ("Python", "TypeScript", "React", "Kubernetes", "Redis", "Go", "Linux"),
    }

    scored: dict[str, int] = {}
    for name, skills in profiles.items():
        # Rebuild passport with requirement skill IDs for owned skills.
        owned = []
        for skill_name in skills:
            skill_id = ids.get(skill_name, uuid4())
            owned.append(
                SkillPassportSkillResponse(
                    id=skill_id,
                    name=skill_name,
                    category="language",
                    evidence_confidence=0.8,
                    evidence_count=1,
                    evidence=[],
                    github_repositories=[],
                )
            )
        passport = SkillPassportResponse(
            skills=owned, total_skills=len(owned), total_evidence=0
        )
        scored[name] = match_passport_to_requirements(passport, requirements).score

    assert scored["Alex Rivera"] == 85
    assert scored["Jordan Lee"] == 75
    assert scored["Sam Okonkwo"] == 65
    assert scored["Casey Nguyen"] == 48
    assert all(score < 100 for score in scored.values())
    assert len(set(scored.values())) == 4
    ordered = sorted(scored.items(), key=lambda item: (-item[1], item[0]))
    assert [name for name, _ in ordered] == [
        "Alex Rivera",
        "Jordan Lee",
        "Sam Okonkwo",
        "Casey Nguyen",
    ]


def test_demo_candidate_emails_are_isolated() -> None:
    assert len(DEMO_CANDIDATE_EMAILS) >= 4
    assert all(is_demo_email(email) for email in DEMO_CANDIDATE_EMAILS)
    assert is_demo_email(DEMO_EMPLOYER_EMAIL)
    assert not is_demo_email("person@example.com")


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    from app.core.config import settings

    monkeypatch.setattr(settings, "jwt_secret", "demo-mode-test-secret-with-32-bytes-min")
    monkeypatch.setattr(settings, "demo_mode", True)
    app.dependency_overrides[get_db] = lambda: object()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_demo_status_still_enabled(client: TestClient) -> None:
    response = client.get("/api/v1/demo/status")
    assert response.status_code == 200
    assert response.json()["enabled"] is True
