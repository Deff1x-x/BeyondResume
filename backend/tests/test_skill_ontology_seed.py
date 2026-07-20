from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import engine
from app.models.candidate_profile import CandidateProfile, OnboardingStatus
from app.models.evidence_skill_link import EvidenceSkillLink
from app.models.evidence_unit import EvidenceUnit
from app.models.skill import Skill
from app.models.skill_alias import SkillAlias
from app.models.user import User
from app.services.skill_extraction import extract_and_link_evidence_skills
from app.services.skill_ontology_seed import (
    SkillOntologySeedDefinition,
    load_skill_ontology_seed,
    seed_skill_ontology,
)
from app.services.skill_passport import build_passport
from app.utils.skill_name import normalize_skill_name


@pytest.fixture
def postgres_session() -> Session:
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


def _count(session: Session, model: type[Skill] | type[SkillAlias]) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0


def test_seed_creates_canonical_skills_aliases_and_is_idempotent(postgres_session: Session) -> None:
    version, default_definitions = load_skill_ontology_seed()
    definitions = (
        SkillOntologySeedDefinition(
            canonical_name="Seed Test Language",
            category="test",
            aliases=("seed test alias",),
        ),
    )
    first = seed_skill_ontology(
        postgres_session, version=version, definitions=definitions
    )
    first_skill_count = _count(postgres_session, Skill)
    first_alias_count = _count(postgres_session, SkillAlias)

    assert first.skills_created > 0
    assert first.aliases_created > 0
    assert postgres_session.scalar(
        select(Skill).where(Skill.normalized_name == normalize_skill_name("Seed Test Language"))
    ) is not None
    assert postgres_session.scalar(
        select(SkillAlias).where(
            SkillAlias.normalized_alias == normalize_skill_name("seed test alias")
        )
    ) is not None

    second = seed_skill_ontology(
        postgres_session, version=version, definitions=definitions
    )

    assert second.skills_created == 0
    assert second.aliases_created == 0
    assert _count(postgres_session, Skill) == first_skill_count
    assert _count(postgres_session, SkillAlias) == first_alias_count
    assert any(item.canonical_name == "Python" for item in default_definitions)


def test_seed_reuses_existing_canonical_skill_and_adds_missing_alias(postgres_session: Session) -> None:
    existing = Skill(
        id=uuid4(),
        canonical_name="Existing Seed Skill",
        normalized_name=normalize_skill_name("Existing Seed Skill"),
        category="custom-category",
        description="Existing data must not be overwritten.",
        ontology_version="custom-v1",
        deprecated=False,
    )
    postgres_session.add(existing)
    postgres_session.flush()

    seed_skill_ontology(
        postgres_session,
        version="test-v1",
        definitions=(
            SkillOntologySeedDefinition(
                canonical_name="Existing Seed Skill",
                category="seed-category",
                aliases=("existing seed alias",),
            ),
        ),
    )

    matching_skills = postgres_session.scalars(
        select(Skill).where(
            Skill.normalized_name == normalize_skill_name("Existing Seed Skill")
        )
    ).all()
    alias = postgres_session.scalar(
        select(SkillAlias).where(
            SkillAlias.normalized_alias == normalize_skill_name("existing seed alias")
        )
    )
    assert matching_skills == [existing]
    assert existing.category == "custom-category"
    assert alias is not None
    assert alias.skill_id == existing.id


def test_seeded_ontology_extracts_links_idempotently_and_populates_passport(
    postgres_session: Session,
) -> None:
    seed_skill_ontology(postgres_session)
    user = User(
        id=uuid4(),
        email=f"seed-extraction-{uuid4()}@example.com",
        password_hash="hash",
        role="candidate",
        status="active",
    )
    candidate = CandidateProfile(
        id=uuid4(), user_id=user.id, onboarding_status=OnboardingStatus.PROFILE_REQUIRED
    )
    evidence = EvidenceUnit(
        id=uuid4(),
        candidate_id=candidate.id,
        source_type="github_repository",
        source_reference=f"https://github.com/example/{uuid4()}",
        title="Repository evidence",
        description=(
            "Python TypeScript JavaScript CSS Next.js FastAPI PostgreSQL Docker"
        ),
        observed_at=datetime.now(UTC),
        verification_status="source_reachable",
        ownership_status="unverified",
        strength_score=Decimal("1.00"),
        quality_flags={},
    )
    postgres_session.add_all([user, candidate, evidence])
    postgres_session.flush()

    first = extract_and_link_evidence_skills(postgres_session, evidence)
    second = extract_and_link_evidence_skills(postgres_session, evidence)
    passport = build_passport(postgres_session, candidate.id)

    expected = {
        "Python", "TypeScript", "JavaScript", "CSS", "Next.js", "FastAPI", "PostgreSQL", "Docker"
    }
    assert {match.skill.canonical_name for match in first.matches} == expected
    assert first.created_count == len(expected)
    assert second.created_count == 0
    assert second.unchanged_count == len(expected)
    assert postgres_session.scalar(
        select(func.count()).select_from(EvidenceSkillLink).where(
            EvidenceSkillLink.evidence_unit_id == evidence.id
        )
    ) == len(expected)
    assert {skill.name for skill in passport.skills} == expected
    assert passport.total_skills == len(expected)
    assert passport.total_evidence == 1
