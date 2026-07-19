from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.models.candidate_profile import CandidateProfile, OnboardingStatus
from app.models.skill import Skill
from app.models.vacancy_skill_requirement import VacancySkillRequirement
from app.schemas.roadmap import RoadmapItemResponse, RoadmapResponse
from app.schemas.skill_passport import (
    SkillPassportEvidenceResponse,
    SkillPassportResponse,
    SkillPassportSkillResponse,
)
from app.services.match_details import (
    MatchDetailsCandidateNotFoundError,
    build_match_details,
)
from app.services.matching import MatchResult, SkillGroupBreakdown


def make_candidate() -> CandidateProfile:
    return CandidateProfile(
        id=uuid4(),
        user_id=uuid4(),
        display_name="Ada Lovelace",
        target_role="Backend Engineer",
        onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
    )


def make_passport() -> SkillPassportResponse:
    evidence_id = uuid4()
    return SkillPassportResponse(
        skills=[
            SkillPassportSkillResponse(
                id=uuid4(),
                name="Python",
                category="language",
                evidence_confidence=1.0,
                evidence_count=1,
                evidence=[
                    SkillPassportEvidenceResponse(
                        id=evidence_id,
                        title="Resume: ada.pdf",
                        description="Python experience",
                        source_type="resume",
                        source_reference=str(uuid4()),
                        evidence_confidence=1.0,
                    )
                ],
            ),
            SkillPassportSkillResponse(
                id=uuid4(),
                name="FastAPI",
                category="framework",
                evidence_confidence=0.9,
                evidence_count=1,
                evidence=[
                    SkillPassportEvidenceResponse(
                        id=evidence_id,
                        title="Resume: ada.pdf",
                        description="Python experience",
                        source_type="resume",
                        source_reference=str(uuid4()),
                        evidence_confidence=0.9,
                    )
                ],
            ),
        ],
        total_skills=2,
        total_evidence=1,
    )


def test_build_match_details_aggregates_existing_services(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services import match_details

    candidate = make_candidate()
    vacancy_id = uuid4()
    passport = make_passport()
    skill = Skill(
        id=uuid4(),
        canonical_name="Python",
        normalized_name="python",
        category="language",
        description=None,
        ontology_version="v1",
        deprecated=False,
    )
    requirement = VacancySkillRequirement(
        id=uuid4(),
        vacancy_id=vacancy_id,
        skill_id=skill.id,
        requirement_type="required",
    )

    session = Mock()
    candidate_result = Mock()
    candidate_result.scalar_one_or_none.return_value = candidate
    session.execute.return_value = candidate_result

    monkeypatch.setattr(match_details, "build_passport", lambda *_args: passport)
    monkeypatch.setattr(
        match_details,
        "list_vacancy_requirements",
        lambda *_args: [(requirement, skill)],
    )
    monkeypatch.setattr(
        match_details,
        "match_passport_to_requirements",
        lambda *_args: MatchResult(
            score=91,
            required=SkillGroupBreakdown(matched=("Python",), missing=()),
            preferred=SkillGroupBreakdown(matched=(), missing=("Docker",)),
        ),
    )
    monkeypatch.setattr(
        match_details,
        "build_roadmap_from_passport",
        lambda *_args: RoadmapResponse(
            items=[
                RoadmapItemResponse(
                    id="add-docker",
                    title="Add Docker evidence",
                    reason="Required for preferred stack depth",
                    priority="medium",
                    missing_skills=["Docker"],
                    related_skills=["Python"],
                )
            ]
        ),
    )

    result = build_match_details(
        session, vacancy_id=vacancy_id, candidate_id=candidate.id
    )

    assert result.candidate.name == "Ada Lovelace"
    assert result.candidate.headline == "Backend Engineer"
    assert result.candidate.avatar is None
    assert result.match.score == 91
    assert result.match.required.matched == ["Python"]
    assert result.match.preferred.missing == ["Docker"]
    assert result.passport.top_skills == ["Python", "FastAPI"]
    assert len(result.evidence) == 1
    assert result.evidence[0].source_type == "resume"
    assert result.evidence[0].skills == ["FastAPI", "Python"]
    assert result.roadmap[0].id == "add-docker"


def test_build_match_details_requires_candidate(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services import match_details

    session = Mock()
    result = Mock()
    result.scalar_one_or_none.return_value = None
    session.execute.return_value = result
    monkeypatch.setattr(match_details, "build_passport", Mock())

    with pytest.raises(MatchDetailsCandidateNotFoundError):
        build_match_details(session, vacancy_id=uuid4(), candidate_id=uuid4())
