"""Idempotent seed and reset for isolated Demo Mode tenants."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.application import Application
from app.models.candidate_profile import CandidateProfile, OnboardingStatus
from app.models.career_companion_action import CareerCompanionAction
from app.models.career_companion_chat_message import CareerCompanionChatMessage
from app.models.career_companion_plan import CareerCompanionPlan
from app.models.career_companion_progress_event import CareerCompanionProgressEvent
from app.models.employer_candidate_shortlist import EmployerCandidateShortlist
from app.models.employer_interview_scorecard import EmployerInterviewScorecard
from app.models.employer_profile import EmployerProfile
from app.models.evidence_skill_link import EvidenceSkillLink
from app.models.evidence_unit import EvidenceUnit
from app.models.github_repository import GitHubRepository
from app.models.github_repository_snapshot import GitHubRepositorySnapshot
from app.models.resume import Resume
from app.models.skill import Skill
from app.models.user import User
from app.models.vacancy import Vacancy
from app.models.vacancy_skill_requirement import VacancySkillRequirement
from app.services.demo_users import (
    DEMO_CANDIDATE_B_EMAIL,
    DEMO_CANDIDATE_C_EMAIL,
    DEMO_CANDIDATE_D_EMAIL,
    DEMO_CANDIDATE_EMAIL,
    DEMO_CANDIDATE_EMAILS,
    DEMO_EMPLOYER_EMAIL,
    DEMO_PASSWORD,
)

# Primary candidate demo passport skills (incomplete vs platform vacancy — no 100%).
_DEMO_PRIMARY_SKILLS = (
    "Python",
    "PostgreSQL",
    "Docker",
    "FastAPI",
    "TypeScript",
    "Redis",
)


def _skill_by_name(session: Session, name: str) -> Skill | None:
    normalized = name.strip().lower()
    return session.scalar(select(Skill).where(Skill.normalized_name == normalized))


def _ensure_user(session: Session, *, email: str, role: str) -> User:
    user = session.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(
            id=uuid4(),
            email=email,
            password_hash=hash_password(DEMO_PASSWORD),
            role=role,
            status="active",
        )
        session.add(user)
        session.flush()
        return user
    user.role = role
    user.status = "active"
    user.password_hash = hash_password(DEMO_PASSWORD)
    session.flush()
    return user


def _purge_candidate_graph(session: Session, candidate: CandidateProfile) -> None:
    plan_ids = list(
        session.scalars(
            select(CareerCompanionPlan.id).where(CareerCompanionPlan.candidate_id == candidate.id)
        )
    )
    if plan_ids:
        session.execute(
            delete(CareerCompanionChatMessage).where(
                CareerCompanionChatMessage.plan_id.in_(plan_ids)
            )
        )
        session.execute(
            delete(CareerCompanionProgressEvent).where(
                CareerCompanionProgressEvent.plan_id.in_(plan_ids)
            )
        )
        session.execute(
            delete(CareerCompanionAction).where(CareerCompanionAction.plan_id.in_(plan_ids))
        )
        session.execute(delete(CareerCompanionPlan).where(CareerCompanionPlan.id.in_(plan_ids)))

    session.execute(delete(Application).where(Application.candidate_id == candidate.id))
    session.execute(
        delete(EmployerCandidateShortlist).where(
            EmployerCandidateShortlist.candidate_id == candidate.id
        )
    )
    session.execute(
        delete(EmployerInterviewScorecard).where(
            EmployerInterviewScorecard.candidate_id == candidate.id
        )
    )
    session.execute(
        delete(EvidenceSkillLink).where(EvidenceSkillLink.candidate_id == candidate.id)
    )
    session.execute(delete(EvidenceUnit).where(EvidenceUnit.candidate_id == candidate.id))

    repo_ids = list(
        session.scalars(
            select(GitHubRepository.id).where(GitHubRepository.candidate_id == candidate.id)
        )
    )
    if repo_ids:
        session.execute(
            delete(GitHubRepositorySnapshot).where(
                GitHubRepositorySnapshot.repository_id.in_(repo_ids)
            )
        )
        session.execute(delete(GitHubRepository).where(GitHubRepository.id.in_(repo_ids)))

    session.execute(delete(Resume).where(Resume.candidate_id == candidate.id))


def _purge_employer_graph(session: Session, employer: EmployerProfile) -> None:
    vacancy_ids = list(
        session.scalars(select(Vacancy.id).where(Vacancy.employer_id == employer.id))
    )
    if vacancy_ids:
        session.execute(
            delete(EmployerInterviewScorecard).where(
                EmployerInterviewScorecard.vacancy_id.in_(vacancy_ids)
            )
        )
        session.execute(
            delete(EmployerCandidateShortlist).where(
                EmployerCandidateShortlist.vacancy_id.in_(vacancy_ids)
            )
        )
        session.execute(delete(Application).where(Application.vacancy_id.in_(vacancy_ids)))
        session.execute(
            delete(VacancySkillRequirement).where(
                VacancySkillRequirement.vacancy_id.in_(vacancy_ids)
            )
        )
        session.execute(delete(Vacancy).where(Vacancy.id.in_(vacancy_ids)))


def _seed_candidate(
    session: Session,
    *,
    email: str,
    display_name: str,
    target_role: str,
    summary: str,
    skill_names: tuple[str, ...],
) -> CandidateProfile:
    user = _ensure_user(session, email=email, role="candidate")
    profile = session.scalar(
        select(CandidateProfile).where(CandidateProfile.user_id == user.id)
    )
    if profile is None:
        profile = CandidateProfile(
            id=uuid4(),
            user_id=user.id,
            onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
        )
        session.add(profile)
        session.flush()

    _purge_candidate_graph(session, profile)

    profile.display_name = display_name
    profile.target_role = target_role
    profile.location = "Remote"
    profile.remote_preference = "remote"
    profile.english_level = "C1"
    profile.availability = "2 weeks"
    profile.summary = summary
    profile.data_processing_consent = True
    profile.preferred_employment_type = "full_time"
    profile.relocation_readiness = False
    profile.linkedin_url = "https://linkedin.com/in/demo-candidate"
    session.flush()

    upload_root = Path(settings.upload_dir) / "demo"
    upload_root.mkdir(parents=True, exist_ok=True)
    resume_path = upload_root / f"{profile.id}-resume.txt"
    resume_body = (
        f"{display_name}\n{target_role}\n\n{summary}\n\nSkills: {', '.join(skill_names)}\n"
    )
    resume_path.write_text(resume_body, encoding="utf-8")

    session.add(
        Resume(
            id=uuid4(),
            candidate_id=profile.id,
            original_filename="demo-resume.pdf",
            stored_path=str(resume_path),
            mime_type="application/pdf",
            file_size_bytes=len(resume_body.encode("utf-8")),
            checksum="demo-checksum",
            is_current=True,
            extracted_text=resume_body,
            parse_status="parsed",
            parsed_at=datetime.now(UTC),
        )
    )

    repo = GitHubRepository(
        id=uuid4(),
        candidate_id=profile.id,
        repository_url="https://github.com/demo-user/demo-api",
    )
    session.add(repo)
    session.flush()
    session.add(
        GitHubRepositorySnapshot(
            id=uuid4(),
            repository_id=repo.id,
            checksum="a" * 64,
            payload={
                "demo": True,
                "commit_sha": "demo0001",
                "languages": {"Python": 60, "TypeScript": 40},
                "files": ["README.md", "src/main.py"],
            },
        )
    )

    now = datetime.now(UTC)
    github_evidence = EvidenceUnit(
        id=uuid4(),
        candidate_id=profile.id,
        source_type="github_repository",
        source_reference="https://github.com/demo-user/demo-api",
        title="demo-user/demo-api",
        description="Public API service demonstrating production-quality Python and TypeScript.",
        observed_at=now,
        freshness_at=now,
        verification_status="ownership_confirmed",
        ownership_status="verified",
        strength_score=Decimal("0.92"),
        quality_flags={
            "demo": True,
            "missing_readme": False,
            "empty_file_tree": False,
            "missing_manifests": False,
        },
    )
    resume_evidence = EvidenceUnit(
        id=uuid4(),
        candidate_id=profile.id,
        source_type="resume",
        source_reference=str(resume_path),
        title="Professional resume",
        description="Parsed resume evidence for the demo candidate.",
        observed_at=now,
        freshness_at=now,
        verification_status="platform_assessed",
        ownership_status="verified",
        strength_score=Decimal("0.80"),
        quality_flags={"demo": True},
    )
    session.add_all([github_evidence, resume_evidence])
    session.flush()

    for index, skill_name in enumerate(skill_names):
        skill = _skill_by_name(session, skill_name)
        if skill is None:
            continue
        path = f"src/{skill_name.lower().replace(' ', '_')}/service.py"
        github_signals: list[dict[str, object]] = [
            {"type": "source_import", "path": path},
            {"type": "source_function_usage", "path": path},
            {"type": "dependency_manifest", "manifest": "pyproject.toml"},
            {"type": "test_usage", "path": f"tests/test_{skill_name.lower().replace(' ', '_')}.py"},
        ]
        session.add(
            EvidenceSkillLink(
                id=uuid4(),
                candidate_id=profile.id,
                evidence_unit_id=github_evidence.id,
                skill_id=skill.id,
                extraction_method="deterministic",
                extraction_version="demo-1",
                extraction_confidence=Decimal("0.95"),
                context={
                    "snippet": f"Used {skill_name} in production work.",
                    "demo": True,
                    "signals": github_signals,
                },
            )
        )
        # Secondary resume link for evidence diversity (does not replace GitHub coverage).
        if index % 2 == 1:
            session.add(
                EvidenceSkillLink(
                    id=uuid4(),
                    candidate_id=profile.id,
                    evidence_unit_id=resume_evidence.id,
                    skill_id=skill.id,
                    extraction_method="deterministic",
                    extraction_version="demo-1-resume",
                    extraction_confidence=Decimal("0.90"),
                    context={
                        "snippet": f"Resume mentions {skill_name}.",
                        "demo": True,
                        "signals": [
                            {
                                "type": "source_import",
                                "path": f"resume/{skill_name.lower().replace(' ', '_')}",
                            }
                        ],
                    },
                )
            )

    session.add(
        CareerCompanionPlan(
            id=uuid4(),
            candidate_id=profile.id,
            mode="career_growth",
            target_role=target_role,
            status="active",
            generation_mode="mock",
            context_hash="demo-context-hash",
            summary={
                "headline": f"Grow toward {target_role}",
                "narrative": "Your evidence already supports a strong platform profile. Focus on depth in system design and communication.",
                "priorities": ["Ship a portfolio API", "Document architecture decisions", "Practice behavioral interviews"],
            },
            current_position={
                "role": target_role,
                "strengths": list(skill_names[:3]),
                "gaps": ["System design storytelling"],
            },
        )
    )
    session.flush()

    plan = session.scalar(
        select(CareerCompanionPlan).where(CareerCompanionPlan.candidate_id == profile.id)
    )
    assert plan is not None
    session.add_all(
        [
            CareerCompanionAction(
                id=uuid4(),
                plan_id=plan.id,
                horizon="fix_now",
                action_type="improve_existing_project",
                status="suggested",
                title="Publish a production-style API case study",
                description="Turn your demo-api repository into a hiring-ready case study with architecture notes.",
                why_it_matters="Employers trust skills when they see ownership, trade-offs, and measurable outcomes.",
                implementation_steps=[
                    "Add architecture diagram to README",
                    "Document scaling decisions",
                    "Link evidence in your Skill Passport",
                ],
                expected_artifacts=["Updated README", "Architecture notes"],
                verification_method="Evidence unit + Skill Passport link",
                estimated_effort="medium",
                github_repository_id=repo.id,
                project_label="demo-api",
                current_target_impact={"match_lift": "high"},
                career_growth_impact={"visibility": "high"},
                priority_score=0.92,
                priority_explanation="Highest signal for platform roles.",
                sort_order=0,
            ),
            CareerCompanionAction(
                id=uuid4(),
                plan_id=plan.id,
                horizon="build_next",
                action_type="learn_foundation",
                status="suggested",
                title="Practice system design storytelling",
                description="Prepare two stories that connect evidence to trade-offs and outcomes.",
                why_it_matters="Interviewers need narrative, not only repositories.",
                implementation_steps=[
                    "Draft STAR stories from GitHub evidence",
                    "Rehearse a 5-minute architecture walkthrough",
                ],
                expected_artifacts=["Interview story notes"],
                verification_method="Career Companion progress event",
                estimated_effort="low",
                priority_score=0.78,
                priority_explanation="Closes the main soft gap in the demo profile.",
                sort_order=1,
            ),
        ]
    )
    session.flush()
    return profile


def _seed_employer(
    session: Session,
    *,
    candidates: list[tuple[CandidateProfile, dict[str, object]]],
) -> EmployerProfile:
    user = _ensure_user(session, email=DEMO_EMPLOYER_EMAIL, role="employer")
    employer = session.scalar(select(EmployerProfile).where(EmployerProfile.user_id == user.id))
    if employer is None:
        employer = EmployerProfile(id=uuid4(), user_id=user.id, company_name="Northwind Labs")
        session.add(employer)
        session.flush()

    _purge_employer_graph(session, employer)

    employer.company_name = "Northwind Labs"
    employer.website = "https://northwind.demo"
    employer.description = "Product-minded engineering company hiring evidence-backed talent."
    session.flush()

    vacancy = Vacancy(
        id=uuid4(),
        employer_id=employer.id,
        title="Senior Platform Engineer",
        description=(
            "Build reliable APIs and developer platforms. We value verified skills, clear evidence, "
            "and pragmatic delivery over keyword stuffing."
        ),
        status="open",
    )
    vacancy_b = Vacancy(
        id=uuid4(),
        employer_id=employer.id,
        title="Full-Stack Engineer",
        description="Ship product features across TypeScript and Python services.",
        status="open",
    )
    session.add_all([vacancy, vacancy_b])
    session.flush()

    # 4 required + 4 preferred → deterministic non-perfect scores for partial passports.
    platform_requirements = (
        ("Python", "required"),
        ("PostgreSQL", "required"),
        ("Docker", "required"),
        ("FastAPI", "required"),
        ("TypeScript", "preferred"),
        ("React", "preferred"),
        ("Kubernetes", "preferred"),
        ("Redis", "preferred"),
    )
    fullstack_requirements = (
        ("Python", "required"),
        ("TypeScript", "required"),
        ("React", "required"),
        ("PostgreSQL", "preferred"),
        ("FastAPI", "preferred"),
        ("Docker", "preferred"),
    )
    for skill_name, requirement_type in platform_requirements:
        skill = _skill_by_name(session, skill_name)
        if skill is None:
            continue
        session.add(
            VacancySkillRequirement(
                id=uuid4(),
                vacancy_id=vacancy.id,
                skill_id=skill.id,
                requirement_type=requirement_type,
            )
        )
    for skill_name, requirement_type in fullstack_requirements:
        skill = _skill_by_name(session, skill_name)
        if skill is None:
            continue
        session.add(
            VacancySkillRequirement(
                id=uuid4(),
                vacancy_id=vacancy_b.id,
                skill_id=skill.id,
                requirement_type=requirement_type,
            )
        )

    for index, (candidate, meta) in enumerate(candidates):
        session.add(
            Application(
                id=uuid4(),
                vacancy_id=vacancy.id,
                candidate_id=candidate.id,
                status="applied",
            )
        )
        if index == 0:
            session.add(
                Application(
                    id=uuid4(),
                    vacancy_id=vacancy_b.id,
                    candidate_id=candidate.id,
                    status="applied",
                )
            )

        session.add(
            EmployerCandidateShortlist(
                id=uuid4(),
                employer_id=employer.id,
                vacancy_id=vacancy.id,
                candidate_id=candidate.id,
                stage=str(meta["stage"]),
                note=str(meta["note"]),
            )
        )
        if meta.get("scorecard"):
            session.add(
                EmployerInterviewScorecard(
                    id=uuid4(),
                    employer_id=employer.id,
                    vacancy_id=vacancy.id,
                    candidate_id=candidate.id,
                    technical_competency=5,
                    experience_relevance=4,
                    communication=4,
                    ownership=5,
                    interview_summary="Clear ownership of platform work with strong Python evidence.",
                    interview_notes="Probe system design depth and stakeholder communication next round.",
                    recommendation="strong_yes",
                )
            )
    session.flush()
    return employer


def ensure_demo_tenants(session: Session) -> dict[str, User]:
    """Create or refresh isolated demo tenants. Safe to call repeatedly."""
    # Expected Senior Platform scores (4 required + 4 preferred, 70/30 weights):
    # A: 4/4 + 2/4 = 85 | B: 3/4 + 3/4 = 75 | C: 2/4 + 4/4 = 65 | D: 1/4 + 4/4 = 48
    primary = _seed_candidate(
        session,
        email=DEMO_CANDIDATE_EMAIL,
        display_name="Alex Rivera",
        target_role="Platform Engineer",
        summary=(
            "Platform engineer with strong Python/FastAPI/PostgreSQL evidence. Solid Docker "
            "ownership; lighter frontend and orchestration coverage."
        ),
        skill_names=_DEMO_PRIMARY_SKILLS,
    )
    secondary = _seed_candidate(
        session,
        email=DEMO_CANDIDATE_B_EMAIL,
        display_name="Jordan Lee",
        target_role="Full-Stack Engineer",
        summary=(
            "Product-focused full-stack engineer with React/TypeScript depth and workable "
            "Python APIs. Less infrastructure specialization than pure platform profiles."
        ),
        skill_names=("Python", "PostgreSQL", "FastAPI", "TypeScript", "React", "Redis"),
    )
    tertiary = _seed_candidate(
        session,
        email=DEMO_CANDIDATE_C_EMAIL,
        display_name="Sam Okonkwo",
        target_role="Junior Backend Engineer",
        summary=(
            "High-potential junior with solid project evidence in Python and PostgreSQL plus "
            "broad preferred tooling. Still building production FastAPI and Docker depth."
        ),
        skill_names=("Python", "PostgreSQL", "TypeScript", "React", "Redis", "Kubernetes"),
    )
    quaternary = _seed_candidate(
        session,
        email=DEMO_CANDIDATE_D_EMAIL,
        display_name="Casey Nguyen",
        target_role="Software Engineer",
        summary=(
            "Versatile generalist with transferable engineering skills across Go, Linux, and "
            "frontend stacks. Several platform-required skills are still missing."
        ),
        skill_names=("Python", "TypeScript", "React", "Kubernetes", "Redis", "Go", "Linux"),
    )
    employer = _seed_employer(
        session,
        candidates=[
            (
                primary,
                {
                    "stage": "interview",
                    "note": "Strong backend depth; missing preferred React/Kubernetes.",
                    "scorecard": True,
                },
            ),
            (
                secondary,
                {
                    "stage": "screening",
                    "note": "Versatile full-stack profile; missing required Docker.",
                    "scorecard": False,
                },
            ),
            (
                tertiary,
                {
                    "stage": "shortlisted",
                    "note": "High potential; gaps on FastAPI and Docker production evidence.",
                    "scorecard": False,
                },
            ),
            (
                quaternary,
                {
                    "stage": "shortlisted",
                    "note": "Adjacent profile — multiple required platform skills missing.",
                    "scorecard": False,
                },
            ),
        ],
    )
    session.commit()

    users = {
        "candidate": session.get(User, primary.user_id),
        "candidate_b": session.get(User, secondary.user_id),
        "candidate_c": session.get(User, tertiary.user_id),
        "candidate_d": session.get(User, quaternary.user_id),
        "employer": session.get(User, employer.user_id),
    }
    assert all(users.values())
    return users  # type: ignore[return-value]


def reset_demo_tenants(session: Session) -> dict[str, User]:
    """Hard-reset demo tenants to the canonical fixture state."""
    return ensure_demo_tenants(session)


def get_demo_user_for_role(session: Session, role: str) -> User:
    tenants = ensure_demo_tenants(session)
    if role == "employer":
        return tenants["employer"]
    return tenants["candidate"]


def demo_user_emails() -> tuple[str, ...]:
    return (*DEMO_CANDIDATE_EMAILS, DEMO_EMPLOYER_EMAIL)
