import ast
from pathlib import Path
import re
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
from app.utils.github_code_usage_rules import GitHubCodeUsageRule


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


def _stub_link_contexts(
    monkeypatch: pytest.MonkeyPatch,
    contexts: dict[tuple[UUID, UUID], list] | None = None,
) -> None:
    from app.services import match_details

    monkeypatch.setattr(
        match_details,
        "_fetch_evidence_link_contexts",
        lambda *_args, **_kwargs: contexts or {},
    )


def _run_match(
    monkeypatch: pytest.MonkeyPatch,
    *,
    candidate: CandidateProfile,
    vacancy_id: UUID,
    passport: SkillPassportResponse,
    requirements: list,
    match_result: MatchResult,
    link_contexts: dict[tuple[UUID, UUID], list] | None = None,
    session: Mock | None = None,
    link_context_loader: Mock | None = None,
):
    from app.services import match_details

    monkeypatch.setattr(match_details, "build_passport", lambda *_args: passport)
    monkeypatch.setattr(match_details, "list_vacancy_requirements", lambda *_args: requirements)
    monkeypatch.setattr(
        match_details, "match_passport_to_requirements", lambda *_args: match_result
    )
    if link_context_loader is not None:
        monkeypatch.setattr(match_details, "_fetch_evidence_link_contexts", link_context_loader)
    else:
        _stub_link_contexts(monkeypatch, link_contexts)
    return build_match_details(
        session or _session_with_candidate(candidate),
        vacancy_id=vacancy_id,
        candidate_id=candidate.id,
    )


def test_build_match_details_aggregates_existing_services(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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

    result = _run_match(
        monkeypatch,
        candidate=candidate,
        vacancy_id=vacancy_id,
        passport=passport,
        requirements=[(requirement, skill)],
        match_result=MatchResult(
            score=91,
            required=SkillGroupBreakdown(matched=("Python",), missing=("C#",)),
            preferred=SkillGroupBreakdown(matched=(), missing=()),
        ),
    )

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
    assert [item.category for item in detail.evidence[0].signal_summaries] == ["resume_evidence"]
    assert result.match.preferred.matched_details == []


def test_matched_details_required_and_preferred_groups(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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

    result = _run_match(
        monkeypatch,
        candidate=candidate,
        vacancy_id=vacancy_id,
        passport=passport,
        requirements=requirements,
        match_result=MatchResult(
            score=85,
            required=SkillGroupBreakdown(matched=("Python",), missing=("C#",)),
            preferred=SkillGroupBreakdown(matched=("FastAPI",), missing=()),
        ),
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

    result = _run_match(
        monkeypatch,
        candidate=candidate,
        vacancy_id=vacancy_id,
        passport=passport,
        requirements=[(requirement, skill)],
        match_result=MatchResult(
            score=100,
            required=SkillGroupBreakdown(matched=("React",), missing=()),
            preferred=SkillGroupBreakdown(matched=(), missing=()),
        ),
        link_contexts={
            (skill_id, evidence_a.id): [
                {
                    "signals": [
                        {
                            "type": "source_import",
                            "manifest": "src/App.tsx",
                            "matched_value": "react",
                            "rule_id": "secret.rule",
                        }
                    ]
                }
            ]
        },
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
    assert [item.category for item in detail.evidence[0].signal_summaries] == ["source_code_usage"]
    assert detail.evidence[1].verification_status is None
    assert detail.evidence[1].ownership_status is None
    assert detail.evidence[1].signal_summaries == []


def test_matched_details_nested_evidence_is_employer_safe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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

    result = _run_match(
        monkeypatch,
        candidate=candidate,
        vacancy_id=vacancy_id,
        passport=passport,
        requirements=[(requirement, skill)],
        match_result=MatchResult(
            score=100,
            required=SkillGroupBreakdown(matched=("Python",), missing=()),
            preferred=SkillGroupBreakdown(matched=(), missing=()),
        ),
        link_contexts={
            (skill_id, evidence.id): [
                {
                    "extractor": "evidence_skill_v1",
                    "version": "evidence-skill-v1",
                    "matched_term": "Python",
                    "match_kind": "alias",
                    "signals": [
                        {
                            "type": "dependency_manifest",
                            "manifest": "package.json",
                            "path": "src/secret.py",
                            "filename": "secret.py",
                            "matched_value": "react",
                            "rule_id": "gh_rule.secret",
                            "ecosystem": "npm",
                            "manifest_kind": "package_json",
                        }
                    ],
                }
            ]
        },
    )
    nested = result.match.required.matched_details[0].evidence[0].model_dump()
    assert set(nested) == {
        "id",
        "source_type",
        "title",
        "verification_status",
        "ownership_status",
        "evidence_confidence",
        "signal_summaries",
    }
    assert nested["signal_summaries"] == [{"category": "resume_evidence"}]
    serialized = str(nested)
    for forbidden in (
        "description",
        "source_reference",
        "context",
        "signals",
        "raw_payload_reference",
        "manifest",
        "matched_value",
        "rule_id",
        "ecosystem",
        "manifest_kind",
        "matched_term",
        "match_kind",
        "extractor",
        "version",
        "filename",
        "path",
        "package.json",
        "secret.py",
    ):
        assert forbidden not in serialized


def test_signal_summaries_github_mixed_and_isolated_by_skill(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = make_candidate()
    vacancy_id = uuid4()
    python_id = uuid4()
    react_id = uuid4()
    shared_evidence_id = uuid4()
    python_only_evidence = make_evidence(
        title="GitHub repository: demo/backend",
        source_type="github_repository",
        evidence_confidence=0.8,
    )
    shared = make_evidence(
        evidence_id=shared_evidence_id,
        title="GitHub repository: demo/shared",
        source_type="github_repository",
        evidence_confidence=0.7,
    )
    passport = SkillPassportResponse(
        skills=[
            SkillPassportSkillResponse(
                id=python_id,
                name="Python",
                category="language",
                evidence_confidence=0.85,
                evidence_count=2,
                evidence=[python_only_evidence, shared],
            ),
            SkillPassportSkillResponse(
                id=react_id,
                name="React",
                category="frontend",
                evidence_confidence=0.7,
                evidence_count=1,
                evidence=[
                    make_evidence(
                        evidence_id=shared_evidence_id,
                        title="GitHub repository: demo/shared",
                        source_type="github_repository",
                        evidence_confidence=0.7,
                    )
                ],
            ),
        ],
        total_skills=2,
        total_evidence=2,
    )
    python = make_skill(skill_id=python_id, name="Python")
    react = make_skill(skill_id=react_id, name="React", category="frontend")
    sensitive_context = {
        "extractor": "github_deterministic",
        "version": "github-deterministic-v1",
        "signals": [
            {
                "type": "dependency_manifest",
                "manifest": "requirements.txt",
                "manifest_kind": "requirements_txt",
                "ecosystem": "pypi",
                "matched_value": "fastapi",
                "rule_id": "gh_rule.dep.fastapi.v1",
            },
            {
                "type": "source_import",
                "manifest": "app/main.py",
                "manifest_kind": "source_file",
                "ecosystem": "github",
                "matched_value": "source_import",
                "rule_id": "gh_rule.code.python.import.v1",
            },
            {
                "type": "source_api_call",
                "manifest": "app/api.py",
                "manifest_kind": "source_file",
                "ecosystem": "github",
                "matched_value": "source_api_call",
                "rule_id": "gh_rule.code.python.api.v1",
            },
            {
                "type": "docker",
                "manifest": "Dockerfile",
                "manifest_kind": "source_file",
                "ecosystem": "github",
                "matched_value": "docker_artifact",
                "rule_id": "gh_rule.code.docker.artifact.v1",
            },
            {
                "type": "future_unknown_signal",
                "manifest": "secret.path",
                "matched_value": "leak",
                "rule_id": "nope",
            },
        ],
    }
    react_only_context = {
        "signals": [
            {
                "type": "dependency_manifest",
                "manifest": "package.json",
                "matched_value": "react",
                "rule_id": "gh_rule.dep.react.v1",
                "ecosystem": "npm",
                "manifest_kind": "package_json",
            }
        ]
    }

    result = _run_match(
        monkeypatch,
        candidate=candidate,
        vacancy_id=vacancy_id,
        passport=passport,
        requirements=[
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
                    skill_id=react.id,
                    requirement_type="preferred",
                ),
                react,
            ),
        ],
        match_result=MatchResult(
            score=90,
            required=SkillGroupBreakdown(matched=("Python",), missing=()),
            preferred=SkillGroupBreakdown(matched=("React",), missing=()),
        ),
        link_contexts={
            (python_id, python_only_evidence.id): [
                sensitive_context,
                # Second extraction version for the same pair merges without duplicates.
                {
                    "signals": [
                        {"type": "dependency_manifest", "manifest": "pyproject.toml"},
                        {"type": "ci", "manifest": ".github/workflows/ci.yml"},
                    ]
                },
            ],
            (python_id, shared_evidence_id): [sensitive_context],
            (react_id, shared_evidence_id): [react_only_context],
            # Unmatched / other-candidate style noise must not appear (not referenced).
            (uuid4(), shared_evidence_id): [sensitive_context],
        },
    )

    assert result.match.score == 90
    assert result.match.required.matched == ["Python"]
    assert result.match.preferred.matched == ["React"]
    python_detail = result.match.required.matched_details[0]
    react_detail = result.match.preferred.matched_details[0]
    assert [item.category for item in python_detail.evidence[0].signal_summaries] == [
        "project_dependencies",
        "source_code_usage",
        "container_configuration",
        "ci_cd_configuration",
    ]
    assert [item.category for item in python_detail.evidence[1].signal_summaries] == [
        "project_dependencies",
        "source_code_usage",
        "container_configuration",
    ]
    assert [item.category for item in react_detail.evidence[0].signal_summaries] == [
        "project_dependencies"
    ]
    # Flat evidence unchanged and free of signal summaries.
    assert "signal_summaries" not in result.evidence[0].model_dump()
    leaked = str(result.model_dump())
    for forbidden in (
        "requirements.txt",
        "package.json",
        "matched_value",
        "rule_id",
        "future_unknown_signal",
        "secret.path",
    ):
        assert forbidden not in leaked


def _gap_requirements(vacancy_id: UUID, skills: list[tuple[Skill, str]]) -> list:
    return [
        (
            VacancySkillRequirement(
                id=uuid4(),
                vacancy_id=vacancy_id,
                skill_id=skill.id,
                requirement_type=requirement_type,
            ),
            skill,
        )
        for skill, requirement_type in skills
    ]


def _run_gap_match(
    monkeypatch: pytest.MonkeyPatch,
    *,
    session: Mock | None = None,
    link_context_loader: Mock | None = None,
    extra_required: list[Skill] | None = None,
):
    """React is owned; Docker and C# are required gaps, GitHub Actions/Pytest preferred."""
    candidate = make_candidate()
    vacancy_id = uuid4()
    react_id = uuid4()
    passport = SkillPassportResponse(
        skills=[
            SkillPassportSkillResponse(
                id=react_id,
                name="React",
                category="frontend",
                evidence_confidence=0.9,
                evidence_count=1,
                evidence=[make_evidence(source_type="github_repository")],
            )
        ],
        total_skills=1,
        total_evidence=1,
    )
    react = make_skill(skill_id=react_id, name="React", category="frontend")
    docker = make_skill(name="Docker", category="infrastructure")
    csharp = make_skill(name="C#")
    actions = make_skill(name="GitHub Actions", category="infrastructure")
    pytest_skill = make_skill(name="Pytest", category="testing")
    ordered = [
        (docker, "required"),
        (csharp, "required"),
        (react, "required"),
        *[(skill, "required") for skill in extra_required or []],
        (actions, "preferred"),
        (pytest_skill, "preferred"),
    ]
    required_missing = tuple(
        skill.canonical_name
        for skill, requirement_type in ordered
        if requirement_type == "required" and skill.id != react_id
    )
    result = _run_match(
        monkeypatch,
        candidate=candidate,
        vacancy_id=vacancy_id,
        passport=passport,
        requirements=_gap_requirements(vacancy_id, ordered),
        match_result=MatchResult(
            score=25,
            required=SkillGroupBreakdown(matched=("React",), missing=required_missing),
            preferred=SkillGroupBreakdown(matched=(), missing=("GitHub Actions", "Pytest")),
        ),
        session=session,
        link_context_loader=link_context_loader,
    )
    return result, react_id, docker.id


def test_missing_details_explain_required_gaps(monkeypatch: pytest.MonkeyPatch) -> None:
    result, _react_id, docker_id = _run_gap_match(monkeypatch)

    required = result.match.required
    assert [item.skill_name for item in required.missing_details] == ["Docker", "C#"]
    assert required.missing_details[0].skill_id == docker_id
    assert [
        suggestion.category for suggestion in required.missing_details[0].evidence_suggestions
    ] == ["resume_evidence", "container_configuration", "ci_cd_configuration"]


def test_missing_details_explain_preferred_gaps(monkeypatch: pytest.MonkeyPatch) -> None:
    result, _react_id, _docker_id = _run_gap_match(monkeypatch)

    preferred = result.match.preferred
    assert [item.skill_name for item in preferred.missing_details] == ["GitHub Actions", "Pytest"]
    assert [
        suggestion.category for suggestion in preferred.missing_details[0].evidence_suggestions
    ] == ["resume_evidence", "ci_cd_configuration"]
    # Pytest has source, config, and CI detectors — and only those.
    assert [
        suggestion.category for suggestion in preferred.missing_details[1].evidence_suggestions
    ] == [
        "resume_evidence",
        "source_code_usage",
        "test_usage",
        "application_configuration",
        "ci_cd_configuration",
    ]


def test_missing_details_exclude_matched_skills(monkeypatch: pytest.MonkeyPatch) -> None:
    result, _react_id, _docker_id = _run_gap_match(monkeypatch)

    every_gap = [
        item.skill_name
        for group in (result.match.required, result.match.preferred)
        for item in group.missing_details
    ]
    assert "React" not in every_gap


def test_missing_details_do_not_mix_required_and_preferred(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, _react_id, _docker_id = _run_gap_match(monkeypatch)

    required_names = {item.skill_name for item in result.match.required.missing_details}
    preferred_names = {item.skill_name for item in result.match.preferred.missing_details}
    assert required_names == {"Docker", "C#"}
    assert preferred_names == {"GitHub Actions", "Pytest"}
    assert required_names.isdisjoint(preferred_names)


def test_missing_stays_a_string_list_aligned_with_missing_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, _react_id, _docker_id = _run_gap_match(monkeypatch)

    for group in (result.match.required, result.match.preferred):
        assert all(isinstance(name, str) for name in group.missing)
        assert group.missing == [item.skill_name for item in group.missing_details]
        for index, name in enumerate(group.missing):
            assert group.missing_details[index].skill_name == name


def test_missing_details_order_survives_extra_requirements(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    extra = [make_skill(name="Kotlin"), make_skill(name="Redis", category="database")]
    result, _react_id, _docker_id = _run_gap_match(monkeypatch, extra_required=extra)

    assert result.match.required.missing == ["Docker", "C#", "Kotlin", "Redis"]
    assert [item.skill_name for item in result.match.required.missing_details] == [
        "Docker",
        "C#",
        "Kotlin",
        "Redis",
    ]


def test_skill_without_github_rules_suggests_resume_evidence_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, _react_id, _docker_id = _run_gap_match(monkeypatch)

    csharp = result.match.required.missing_details[1]
    assert csharp.skill_name == "C#"
    assert [suggestion.category for suggestion in csharp.evidence_suggestions] == [
        "resume_evidence"
    ]


def test_missing_details_do_not_change_score_matching_or_existing_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, react_id, _docker_id = _run_gap_match(monkeypatch)

    assert result.match.score == 25
    assert result.match.required.matched == ["React"]
    assert result.match.required.missing == ["Docker", "C#"]
    assert result.match.preferred.matched == []
    assert result.match.preferred.missing == ["GitHub Actions", "Pytest"]
    # matched_details and flat evidence keep their previous shape.
    assert [item.skill_name for item in result.match.required.matched_details] == ["React"]
    assert result.match.required.matched_details[0].skill_id == react_id
    assert result.match.preferred.matched_details == []
    assert len(result.evidence) == 1
    assert result.evidence[0].skills == ["React"]
    assert "evidence_suggestions" not in result.evidence[0].model_dump()
    assert "missing_details" not in result.passport.model_dump()


def test_gap_suggestions_do_not_read_candidate_evidence_or_add_queries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = Mock()
    candidate_result = Mock()
    candidate_result.scalar_one_or_none.return_value = make_candidate()
    session.execute.return_value = candidate_result
    loader = Mock(return_value={})

    def run(session_mock: Mock) -> object:
        candidate = make_candidate()
        candidate_result.scalar_one_or_none.return_value = candidate
        return _run_gap_match(monkeypatch, session=session_mock, link_context_loader=loader)

    result, react_id, _docker_id = run(session)

    # Only the candidate lookup hits the session; gaps add no EvidenceUnit or
    # EvidenceSkillLink query, and the link-context loader is scoped to matches.
    assert session.execute.call_count == 1
    assert loader.call_count == 1
    assert loader.call_args.kwargs["skill_ids"] == {react_id}
    assert result.match.required.missing_details[0].skill_name == "Docker"


def test_gap_helper_module_has_no_session_or_ai_dependency() -> None:
    from app.services import skill_gap_suggestions

    tree = ast.parse(Path(skill_gap_suggestions.__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)

    assert imported == {
        "__future__",
        "app.services.signal_summaries",
        "app.utils.github_code_usage_rules",
        "app.utils.github_skill_rules",
    }
    for forbidden in ("sqlalchemy", "app.models", "openai", "httpx", "requests"):
        assert not any(module.startswith(forbidden) for module in imported)


def test_missing_details_are_employer_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services import skill_gap_suggestions
    from app.services.skill_gap_suggestions import _code_rule_capabilities

    sensitive_rule = GitHubCodeUsageRule(
        "Synthetic Skill",
        frozenset({".py", ".tsx"}),
        imports=(re.compile(r"\bimport\s+secretpkg\b"),),
        api_calls=(re.compile(r"\bSecretClient\s*\("),),
        class_or_function_usage=(re.compile(r"\bsecret_function\b"),),
        config_files=(re.compile(r"(?:^|/)secret\.config\.json$"),),
        config_patterns=(re.compile(r"secret://"),),
        ci_patterns=(re.compile(r"\bsecret-ci-job\b"),),
    )
    monkeypatch.setattr(
        skill_gap_suggestions,
        "_CAPABILITIES_BY_SKILL_NAME",
        {
            **skill_gap_suggestions._CAPABILITIES_BY_SKILL_NAME,
            "Synthetic Skill": _code_rule_capabilities(sensitive_rule),
        },
    )

    result, _react_id, _docker_id = _run_gap_match(
        monkeypatch,
        extra_required=[make_skill(name="Synthetic Skill", category="framework")],
    )

    details = [
        item.model_dump()
        for group in (result.match.required, result.match.preferred)
        for item in group.missing_details
    ]
    synthetic = next(item for item in details if item["skill_name"] == "Synthetic Skill")
    assert synthetic["evidence_suggestions"] == [
        {"category": "resume_evidence"},
        {"category": "source_code_usage"},
        {"category": "test_usage"},
        {"category": "application_configuration"},
        {"category": "ci_cd_configuration"},
    ]
    for item in details:
        assert set(item) == {"skill_id", "skill_name", "evidence_suggestions"}
        for suggestion in item["evidence_suggestions"]:
            assert set(suggestion) == {"category"}

    serialized = str(details)
    for forbidden in (
        "regex",
        "pattern",
        "patterns",
        "package",
        "dependency",
        "import",
        "api_call",
        "class",
        "function",
        "extension",
        "rule_id",
        "filename",
        "path",
        "manifest",
        "matched_term",
        "match_kind",
        "extractor",
        "version",
        "confidence",
        "weight",
        "context",
        "signals",
        "description",
        "aliases",
        "secretpkg",
        "SecretClient",
        "secret_function",
        "secret.config.json",
        "secret://",
        "secret-ci-job",
        ".py",
        ".tsx",
    ):
        assert forbidden not in serialized


def test_fetch_evidence_link_contexts_filters_candidate_and_skills() -> None:
    from app.services.match_details import _fetch_evidence_link_contexts

    candidate_id = uuid4()
    skill_a = uuid4()
    skill_b = uuid4()
    evidence_id = uuid4()
    session = Mock()
    result = Mock()
    result.all.return_value = [
        (skill_a, evidence_id, {"signals": [{"type": "docker"}]}),
    ]
    session.execute.return_value = result

    contexts = _fetch_evidence_link_contexts(
        session, candidate_id=candidate_id, skill_ids={skill_a, skill_b}
    )

    assert contexts == {(skill_a, evidence_id): [{"signals": [{"type": "docker"}]}]}
    assert session.execute.call_count == 1
    statement = session.execute.call_args.args[0]
    # SQLAlchemy Core/ORM select retains where criteria referencing both filters.
    where_sql = str(statement.compile(compile_kwargs={"literal_binds": False}))
    assert "candidate_id" in where_sql
    assert "skill_id" in where_sql


def test_fetch_evidence_link_contexts_empty_skill_ids_skips_query() -> None:
    from app.services.match_details import _fetch_evidence_link_contexts

    session = Mock()
    assert _fetch_evidence_link_contexts(session, candidate_id=uuid4(), skill_ids=set()) == {}
    session.execute.assert_not_called()


def test_build_match_details_requires_candidate(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services import match_details

    session = Mock()
    result = Mock()
    result.scalar_one_or_none.return_value = None
    session.execute.return_value = result
    monkeypatch.setattr(match_details, "build_passport", Mock())

    with pytest.raises(MatchDetailsCandidateNotFoundError):
        build_match_details(session, vacancy_id=uuid4(), candidate_id=uuid4())
