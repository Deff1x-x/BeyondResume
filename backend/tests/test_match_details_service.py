from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest

from app.models.candidate_profile import CandidateProfile, OnboardingStatus
from app.models.skill import Skill
from app.models.vacancy_skill_requirement import VacancySkillRequirement
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


def make_skill(
    *,
    skill_id: UUID | None = None,
    name: str = "Python",
    category: str = "language",
) -> Skill:
    return Skill(
        id=skill_id or uuid4(),
        canonical_name=name,
        normalized_name=name.lower(),
        category=category,
        description=None,
        ontology_version="v1",
        deprecated=False,
    )


def make_evidence(
    *,
    evidence_id: UUID | None = None,
    title: str = "Resume: ada.pdf",
    source_type: str = "resume",
    source_reference: str | None = None,
    description: str = "secret resume preview",
    verification_status: str | None = "unverified",
    ownership_status: str | None = "verified",
    evidence_confidence: float = 1.0,
) -> SkillPassportEvidenceResponse:
    return SkillPassportEvidenceResponse(
        id=evidence_id or uuid4(),
        title=title,
        description=description,
        source_type=source_type,
        source_reference=source_reference or str(uuid4()),
        verification_status=verification_status,
        ownership_status=ownership_status,
        evidence_confidence=evidence_confidence,
    )


def make_passport(
    *,
    python_id: UUID | None = None,
    fastapi_id: UUID | None = None,
    evidence_id: UUID | None = None,
) -> SkillPassportResponse:
    python_id = python_id or uuid4()
    fastapi_id = fastapi_id or uuid4()
    evidence_id = evidence_id or uuid4()
    shared = make_evidence(evidence_id=evidence_id, evidence_confidence=1.0)
    return SkillPassportResponse(
        skills=[
            SkillPassportSkillResponse(
                id=python_id,
                name="Python",
                category="language",
                evidence_confidence=1.0,
                evidence_count=1,
                evidence=[shared],
            ),
            SkillPassportSkillResponse(
                id=fastapi_id,
                name="FastAPI",
                category="framework",
                evidence_confidence=0.9,
                evidence_count=1,
                evidence=[
                    make_evidence(
                        evidence_id=evidence_id,
                        evidence_confidence=0.9,
                    )
                ],
            ),
        ],
        total_skills=2,
        total_evidence=1,
    )


def _session_with_candidate(candidate: CandidateProfile) -> Mock:
    session = Mock()
    candidate_result = Mock()
    candidate_result.scalar_one_or_none.return_value = candidate
    session.execute.return_value = candidate_result
    return session


def test_build_match_details_aggregates_existing_services(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services import match_details

    candidate = make_candidate()
    vacancy_id = uuid4()
    python_id = uuid4()
    passport = make_passport(python_id=python_id)
    skill = make_skill(skill_id=python_id, name="Python")
    requirement = VacancySkillRequirement(
        id=uuid4(),
        vacancy_id=vacancy_id,
        skill_id=skill.id,
        requirement_type="required",
    )

    session = _session_with_candidate(candidate)
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
            required=SkillGroupBreakdown(matched=("Python",), missing=("C#",)),
            preferred=SkillGroupBreakdown(matched=(), missing=()),
        ),
    )

    result = build_match_details(session, vacancy_id=vacancy_id, candidate_id=candidate.id)

    assert result.candidate.name == "Ada Lovelace"
    assert result.candidate.headline == "Backend Engineer"
    assert result.candidate.avatar is None
    assert result.match.score == 91
    assert result.match.required.matched == ["Python"]
    assert result.match.required.missing == ["C#"]
    assert result.passport.top_skills == ["Python", "FastAPI"]
    assert [item.name for item in result.passport.skills] == ["Python", "FastAPI"]
    assert result.passport.skills[0].evidence_confidence == 1.0
    assert result.passport.skills[0].evidence_count == 1
    assert result.passport.skills[0].source_types == ["resume"]
    # The employer projection does not expose candidate-private evidence details.
    assert "source_reference" not in result.passport.skills[0].model_dump()
    assert "description" not in result.passport.skills[0].model_dump()
    assert len(result.evidence) == 1
    assert result.evidence[0].source_type == "resume"
    assert result.evidence[0].verification_status == "unverified"
    assert result.evidence[0].ownership_status == "verified"
    assert result.evidence[0].skills == ["FastAPI", "Python"]
    assert result.roadmap[0].id == "roadmap.vacancy_gap.csharp.v1"
    assert result.roadmap[0].missing_skills == ["C#"]

    assert len(result.match.required.matched_details) == 1
    detail = result.match.required.matched_details[0]
    assert detail.skill_id == python_id
    assert detail.skill_name == "Python"
    assert len(detail.evidence) == 1
    assert detail.evidence[0].id == passport.skills[0].evidence[0].id
    assert result.match.preferred.matched_details == []


def test_matched_details_required_and_preferred_groups(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services import match_details

    candidate = make_candidate()
    vacancy_id = uuid4()
    python_id = uuid4()
    fastapi_id = uuid4()
    evidence_id = uuid4()
    passport = make_passport(python_id=python_id, fastapi_id=fastapi_id, evidence_id=evidence_id)
    python = make_skill(skill_id=python_id, name="Python")
    fastapi = make_skill(skill_id=fastapi_id, name="FastAPI", category="framework")
    csharp = make_skill(name="C#")
    requirements = [
        (
            VacancySkillRequirement(
                id=uuid4(),
                vacancy_id=vacancy_id,
                skill_id=python.id,
                requirement_type="required",
            ),
            python,
        ),
        (
            VacancySkillRequirement(
                id=uuid4(),
                vacancy_id=vacancy_id,
                skill_id=csharp.id,
                requirement_type="required",
            ),
            csharp,
        ),
        (
            VacancySkillRequirement(
                id=uuid4(),
                vacancy_id=vacancy_id,
                skill_id=fastapi.id,
                requirement_type="preferred",
            ),
            fastapi,
        ),
    ]

    monkeypatch.setattr(match_details, "build_passport", lambda *_args: passport)
    monkeypatch.setattr(match_details, "list_vacancy_requirements", lambda *_args: requirements)
    monkeypatch.setattr(
        match_details,
        "match_passport_to_requirements",
        lambda *_args: MatchResult(
            score=85,
            required=SkillGroupBreakdown(matched=("Python",), missing=("C#",)),
            preferred=SkillGroupBreakdown(matched=("FastAPI",), missing=()),
        ),
    )

    result = build_match_details(
        _session_with_candidate(candidate),
        vacancy_id=vacancy_id,
        candidate_id=candidate.id,
    )

    assert result.match.score == 85
    assert result.match.required.matched == ["Python"]
    assert result.match.required.missing == ["C#"]
    assert result.match.preferred.matched == ["FastAPI"]
    assert [item.skill_name for item in result.match.required.matched_details] == ["Python"]
    assert [item.skill_name for item in result.match.preferred.matched_details] == ["FastAPI"]
    assert all(item.skill_name != "C#" for item in result.match.required.matched_details)
    assert result.match.required.matched_details[0].skill_id == python_id
    assert result.match.preferred.matched_details[0].skill_id == fastapi_id
    # Shared EvidenceUnit appears under each matched skill independently.
    assert result.match.required.matched_details[0].evidence[0].id == evidence_id
    assert result.match.preferred.matched_details[0].evidence[0].id == evidence_id


def test_matched_details_preserves_multi_evidence_and_repos(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services import match_details

    candidate = make_candidate()
    vacancy_id = uuid4()
    skill_id = uuid4()
    evidence_a = make_evidence(
        title="GitHub repository: demo/frontend",
        source_type="github_repository",
        source_reference="https://github.com/demo/frontend",
        description="should not leak",
        verification_status="issuer_verified",
        ownership_status="verified",
        evidence_confidence=0.92,
    )
    evidence_b = make_evidence(
        title="GitHub repository: demo/config",
        source_type="github_repository",
        source_reference="https://github.com/demo/config",
        description="should not leak",
        verification_status=None,
        ownership_status=None,
        evidence_confidence=0.41,
    )
    passport = SkillPassportResponse(
        skills=[
            SkillPassportSkillResponse(
                id=skill_id,
                name="React",
                category="frontend",
                evidence_confidence=0.8,
                evidence_count=2,
                evidence=[evidence_a, evidence_b],
            )
        ],
        total_skills=1,
        total_evidence=2,
    )
    skill = make_skill(skill_id=skill_id, name="React", category="frontend")
    requirement = VacancySkillRequirement(
        id=uuid4(),
        vacancy_id=vacancy_id,
        skill_id=skill.id,
        requirement_type="required",
    )

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
            score=100,
            required=SkillGroupBreakdown(matched=("React",), missing=()),
            preferred=SkillGroupBreakdown(matched=(), missing=()),
        ),
    )

    result = build_match_details(
        _session_with_candidate(candidate),
        vacancy_id=vacancy_id,
        candidate_id=candidate.id,
    )

    detail = result.match.required.matched_details[0]
    assert detail.skill_id == skill_id
    assert detail.skill_name == "React"
    assert [item.id for item in detail.evidence] == [evidence_a.id, evidence_b.id]
    assert [item.title for item in detail.evidence] == [
        "GitHub repository: demo/frontend",
        "GitHub repository: demo/config",
    ]
    assert detail.evidence[0].verification_status == "issuer_verified"
    assert detail.evidence[0].ownership_status == "verified"
    assert detail.evidence[0].evidence_confidence == 0.92
    assert detail.evidence[1].verification_status is None
    assert detail.evidence[1].ownership_status is None


def test_matched_details_nested_evidence_is_employer_safe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services import match_details

    candidate = make_candidate()
    vacancy_id = uuid4()
    skill_id = uuid4()
    evidence = make_evidence(
        title="Resume: ada.pdf",
        description="FULL RESUME TEXT",
        source_reference="resume:secret-id",
        verification_status="unverified",
        ownership_status="unverified",
    )
    passport = SkillPassportResponse(
        skills=[
            SkillPassportSkillResponse(
                id=skill_id,
                name="Python",
                category="language",
                evidence_confidence=1.0,
                evidence_count=1,
                evidence=[evidence],
            )
        ],
        total_skills=1,
        total_evidence=1,
    )
    skill = make_skill(skill_id=skill_id)
    requirement = VacancySkillRequirement(
        id=uuid4(),
        vacancy_id=vacancy_id,
        skill_id=skill.id,
        requirement_type="required",
    )

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
            score=100,
            required=SkillGroupBreakdown(matched=("Python",), missing=()),
            preferred=SkillGroupBreakdown(matched=(), missing=()),
        ),
    )

    result = build_match_details(
        _session_with_candidate(candidate),
        vacancy_id=vacancy_id,
        candidate_id=candidate.id,
    )
    nested = result.match.required.matched_details[0].evidence[0].model_dump()
    assert set(nested) == {
        "id",
        "source_type",
        "title",
        "verification_status",
        "ownership_status",
        "evidence_confidence",
    }
    for forbidden in (
        "description",
        "source_reference",
        "context",
        "signals",
        "raw_payload_reference",
        "manifest",
        "matched_value",
        "rule_id",
    ):
        assert forbidden not in nested


def test_build_match_details_requires_candidate(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services import match_details

    session = Mock()
    result = Mock()
    result.scalar_one_or_none.return_value = None
    session.execute.return_value = result
    monkeypatch.setattr(match_details, "build_passport", Mock())

    with pytest.raises(MatchDetailsCandidateNotFoundError):
        build_match_details(session, vacancy_id=uuid4(), candidate_id=uuid4())
