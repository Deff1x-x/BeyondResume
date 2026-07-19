from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.models.evidence_skill_link import EvidenceSkillLink
from app.models.evidence_unit import EvidenceUnit
from app.models.skill import Skill
from app.models.skill_alias import SkillAlias
from app.services.skill_extraction import (
    EXTRACTION_METHOD,
    EXTRACTION_VERSION,
    ExtractedSkillMatch,
    SkillExtractionService,
    extract_and_link_evidence_skills,
    match_skills_in_text,
)


def make_skill(
    *,
    name: str,
    category: str = "language",
    aliases: list[str] | None = None,
) -> Skill:
    normalized = " ".join(name.strip().lower().replace("-", " ").replace("_", " ").split())
    skill = Skill(
        id=uuid4(),
        canonical_name=name,
        normalized_name=normalized,
        category=category,
        description=None,
        ontology_version="test-v1",
        deprecated=False,
    )
    skill.aliases = [
        SkillAlias(
            id=uuid4(),
            skill_id=skill.id,
            alias=alias,
            normalized_alias=" ".join(
                alias.strip().lower().replace("-", " ").replace("_", " ").split()
            ),
        )
        for alias in (aliases or [])
    ]
    return skill


def make_evidence(*, description: str = "Built APIs with Python and FastAPI") -> EvidenceUnit:
    return EvidenceUnit(
        id=uuid4(),
        candidate_id=uuid4(),
        source_type="resume",
        source_reference=str(uuid4()),
        title="Resume: cv.pdf",
        description=description,
        observed_at=datetime.now(UTC),
        verification_status="unverified",
        ownership_status="unverified",
        strength_score=Decimal("1.00"),
        quality_flags={},
        raw_payload_reference=None,
    )


def session_with_skills(skills: list[Skill]) -> Mock:
    session = Mock()
    result = Mock()
    result.scalars.return_value.all.return_value = skills
    session.execute.return_value = result
    return session


def test_match_skills_by_canonical_name_case_insensitive() -> None:
    python = make_skill(name="Python")
    fastapi = make_skill(name="FastAPI", category="framework")
    # Keep FastAPI normalized as fastapi (make_skill lowercases).
    fastapi.normalized_name = "fastapi"

    matches = match_skills_in_text(
        session_with_skills([python, fastapi]), "Experience with PYTHON and fastapi."
    )

    assert [match.skill.canonical_name for match in matches] == ["FastAPI", "Python"]
    assert all(match.match_kind == "canonical_name" for match in matches)


def test_match_skills_by_alias() -> None:
    python = make_skill(name="Python", aliases=["py"])

    matches = match_skills_in_text(session_with_skills([python]), "Primary language: PY")

    assert len(matches) == 1
    assert matches[0].skill is python
    assert matches[0].match_kind == "alias"
    assert matches[0].matched_term == "py"


def test_match_skills_requires_word_boundary() -> None:
    java = make_skill(name="Java")

    matches = match_skills_in_text(session_with_skills([java]), "javascript experience")

    assert matches == ()


def test_extract_and_link_creates_links_and_removes_stale(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services import skill_extraction

    python = make_skill(name="Python")
    stale_skill = make_skill(name="Ruby")
    evidence = make_evidence(description="Python developer")
    stale_link = EvidenceSkillLink(
        id=uuid4(),
        candidate_id=evidence.candidate_id,
        evidence_unit_id=evidence.id,
        skill_id=stale_skill.id,
        extraction_method=EXTRACTION_METHOD,
        extraction_version=EXTRACTION_VERSION,
        extraction_confidence=Decimal("1.00"),
        context={"extractor": "evidence_skill_v1"},
    )

    session = Mock()
    existing_result = Mock()
    existing_result.scalars.return_value.all.return_value = [stale_link]
    lookup_result = Mock()
    lookup_result.scalar_one_or_none.return_value = None
    session.execute.side_effect = [existing_result, lookup_result]

    monkeypatch.setattr(
        skill_extraction,
        "match_skills_in_text",
        lambda _session, _text: (
            ExtractedSkillMatch(skill=python, matched_term="Python", match_kind="canonical_name"),
        ),
    )
    monkeypatch.setattr(
        skill_extraction,
        "build_evidence_corpus",
        lambda _session, _evidence: evidence.description or "",
    )

    result = extract_and_link_evidence_skills(session, evidence)

    assert result.created_count == 1
    assert result.removed_count == 1
    assert [link.skill_id for link in result.links] == [python.id]
    session.delete.assert_called_once_with(stale_link)
    session.add.assert_called_once()


def test_skill_extraction_service_returns_skills_only(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services import skill_extraction

    python = make_skill(name="Python")
    evidence = make_evidence(description="python")
    monkeypatch.setattr(
        skill_extraction,
        "match_skills_in_text",
        lambda _session, _text: (
            ExtractedSkillMatch(skill=python, matched_term="Python", match_kind="canonical_name"),
        ),
    )
    monkeypatch.setattr(
        skill_extraction,
        "build_evidence_corpus",
        lambda _session, _evidence: "python",
    )

    skills = SkillExtractionService(Mock()).extract_skills(evidence)

    assert [skill.canonical_name for skill in skills] == ["Python"]
