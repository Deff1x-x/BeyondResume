"""Regression tests for employer vacancy match eligibility and uniqueness."""

from collections.abc import Generator
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import engine
from app.models.candidate_profile import CandidateProfile, OnboardingStatus
from app.models.employer_profile import EmployerProfile
from app.models.evidence_skill_link import EvidenceSkillLink
from app.models.evidence_unit import EvidenceUnit
from app.models.skill import Skill
from app.models.user import User
from app.models.vacancy import Vacancy
from app.models.vacancy_skill_requirement import VacancySkillRequirement
from app.services.employer import list_matchable_candidate_profiles, list_vacancy_matches
from app.services.employer_candidate_eligibility import list_employer_eligible_candidates
from app.services.skill_ontology_seed import seed_skill_ontology


@pytest.fixture
def postgres_session() -> Generator[Session, None, None]:
    try:
        connection = engine.connect()
    except SQLAlchemyError as error:
        pytest.skip(f"PostgreSQL is unavailable: {error}")
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


def _add_user(session: Session, *, role: str = "candidate", status: str = "active") -> User:
    user = User(
        id=uuid4(),
        email=f"matches-{role}-{uuid4()}@example.com",
        password_hash="hash",
        role=role,
        status=status,
    )
    session.add(user)
    session.flush()
    return user


def _add_candidate(
    session: Session,
    *,
    display_name: str | None,
    status: str = "active",
) -> CandidateProfile:
    user = _add_user(session, role="candidate", status=status)
    profile = CandidateProfile(
        id=uuid4(),
        user_id=user.id,
        display_name=display_name,
        onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
    )
    session.add(profile)
    session.flush()
    return profile


def _add_vacancy(session: Session) -> Vacancy:
    employer_user = _add_user(session, role="employer")
    employer = EmployerProfile(
        id=uuid4(),
        user_id=employer_user.id,
        company_name=f"Employer {uuid4()}",
    )
    session.add(employer)
    session.flush()
    vacancy = Vacancy(
        id=uuid4(),
        employer_id=employer.id,
        title="Backend Engineer",
        status="open",
    )
    session.add(vacancy)
    session.flush()
    return vacancy


def _add_required_skill(session: Session, vacancy: Vacancy, skill_name: str) -> Skill:
    normalized = skill_name.lower()
    skill = session.execute(
        select(Skill).where(Skill.normalized_name == normalized)
    ).scalar_one_or_none()
    if skill is None:
        skill = Skill(
            id=uuid4(),
            canonical_name=skill_name,
            normalized_name=f"{normalized}-{uuid4().hex[:8]}",
            category="language",
            ontology_version="test",
            deprecated=False,
        )
        session.add(skill)
        session.flush()
    session.add(
        VacancySkillRequirement(
            id=uuid4(),
            vacancy_id=vacancy.id,
            skill_id=skill.id,
            requirement_type="required",
        )
    )
    session.flush()
    return skill


def _add_evidence_with_skill(
    session: Session, candidate: CandidateProfile, skill: Skill, *, source_reference: str
) -> None:
    evidence = EvidenceUnit(
        id=uuid4(),
        candidate_id=candidate.id,
        source_type="github_repository",
        source_reference=source_reference,
        title=f"Evidence {source_reference}",
        verification_status="source_reachable",
        ownership_status="verified",
        strength_score=Decimal("0.80"),
        observed_at=datetime.now(UTC),
    )
    session.add(evidence)
    session.flush()
    session.add(
        EvidenceSkillLink(
            id=uuid4(),
            candidate_id=candidate.id,
            evidence_unit_id=evidence.id,
            skill_id=skill.id,
            extraction_method="deterministic",
            extraction_version="test-v1",
            extraction_confidence=Decimal("0.90"),
            context={"source": "test"},
        )
    )
    session.flush()


def test_empty_registration_shells_are_excluded_from_matches(
    postgres_session: Session,
) -> None:
    vacancy = _add_vacancy(postgres_session)
    named = _add_candidate(postgres_session, display_name="Ada Lovelace")
    unnamed = _add_candidate(postgres_session, display_name=None)
    blank = _add_candidate(postgres_session, display_name="   ")
    suspended = _add_candidate(postgres_session, display_name="Ghost", status="suspended")
    _add_required_skill(postgres_session, vacancy, "Python")
    postgres_session.commit()

    matches = list_vacancy_matches(postgres_session, vacancy.id)
    match_ids = {item.candidate_id for item in matches}

    assert named.id in match_ids
    assert unnamed.id not in match_ids
    assert blank.id not in match_ids
    assert suspended.id not in match_ids
    named_match = next(item for item in matches if item.candidate_id == named.id)
    assert named_match.candidate_name == "Ada Lovelace"
    assert all(
        item.candidate_name != "Unnamed candidate"
        for item in matches
        if item.candidate_id in {named.id, unnamed.id, blank.id, suspended.id}
    )


def test_named_zero_percent_candidate_still_appears(postgres_session: Session) -> None:
    vacancy = _add_vacancy(postgres_session)
    zero_match = _add_candidate(postgres_session, display_name="Zero Match")
    _add_required_skill(postgres_session, vacancy, "Rust")
    postgres_session.commit()

    matches = list_vacancy_matches(postgres_session, vacancy.id)
    zero = next(item for item in matches if item.candidate_id == zero_match.id)

    assert zero.candidate_name == "Zero Match"
    assert zero.result.score == 0
    assert zero.result.required.matched == ()
    assert "Rust" in zero.result.required.missing


def test_two_named_candidates_appear_as_two_cards(postgres_session: Session) -> None:
    vacancy = _add_vacancy(postgres_session)
    first = _add_candidate(postgres_session, display_name="Alex Morgan")
    second = _add_candidate(postgres_session, display_name="Bea Chen")
    _add_required_skill(postgres_session, vacancy, "Python")
    postgres_session.commit()

    matches = list_vacancy_matches(postgres_session, vacancy.id)
    match_ids = {item.candidate_id for item in matches}
    names = {
        item.candidate_name
        for item in matches
        if item.candidate_id in {first.id, second.id}
    }

    assert first.id in match_ids
    assert second.id in match_ids
    assert names == {"Alex Morgan", "Bea Chen"}


def test_candidate_with_multiple_evidence_is_not_duplicated(
    postgres_session: Session,
) -> None:
    vacancy = _add_vacancy(postgres_session)
    candidate = _add_candidate(postgres_session, display_name="Multi Evidence")
    skill = _add_required_skill(postgres_session, vacancy, "Python")
    _add_evidence_with_skill(postgres_session, candidate, skill, source_reference=f"repo-a-{uuid4()}")
    _add_evidence_with_skill(postgres_session, candidate, skill, source_reference=f"repo-b-{uuid4()}")
    _add_evidence_with_skill(postgres_session, candidate, skill, source_reference=f"repo-c-{uuid4()}")
    postgres_session.commit()

    matches = list_vacancy_matches(postgres_session, vacancy.id)
    candidate_matches = [item for item in matches if item.candidate_id == candidate.id]
    matchable = [
        profile
        for profile in list_matchable_candidate_profiles(postgres_session)
        if profile.id == candidate.id
    ]

    assert len(candidate_matches) == 1
    assert candidate_matches[0].candidate_name == "Multi Evidence"
    assert candidate_matches[0].result.score > 0
    assert len(matchable) == 1


def test_canonical_name_is_used_without_unnamed_fallback_for_named_profiles(
    postgres_session: Session,
) -> None:
    vacancy = _add_vacancy(postgres_session)
    candidate = _add_candidate(postgres_session, display_name="  Nora Byte  ")
    _add_required_skill(postgres_session, vacancy, "Go")
    postgres_session.commit()

    matches = list_vacancy_matches(postgres_session, vacancy.id)
    named = next(item for item in matches if item.candidate_id == candidate.id)

    assert named.candidate_name == "Nora Byte"
    assert "Unnamed" not in named.candidate_name


def test_skill_ontology_seed_does_not_create_candidate_profiles(
    postgres_session: Session,
) -> None:
    before_ids = {profile.id for profile in list_employer_eligible_candidates(postgres_session)}
    first = seed_skill_ontology(postgres_session)
    after_first_ids = {
        profile.id for profile in list_employer_eligible_candidates(postgres_session)
    }
    second = seed_skill_ontology(postgres_session)
    after_second_ids = {
        profile.id for profile in list_employer_eligible_candidates(postgres_session)
    }

    assert first.skills_created >= 0
    assert second.skills_created == 0
    assert after_first_ids == before_ids
    assert after_second_ids == before_ids
    assert list_matchable_candidate_profiles(postgres_session) == list_employer_eligible_candidates(
        postgres_session
    )
