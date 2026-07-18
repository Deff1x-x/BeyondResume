from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.exc import IntegrityError

from app.models.evidence_skill_link import EvidenceSkillLink
from app.models.evidence_unit import EvidenceUnit
from app.models.skill import Skill
from app.models.skill_alias import SkillAlias
from app.services.evidence_skill_links import (
    EvidenceSkillLinkCandidateMismatchError,
    InvalidExtractionConfidenceError,
    InvalidExtractionContextError,
    InvalidExtractionMethodError,
    InvalidExtractionVersionError,
    persist_evidence_skill_link,
)
from app.services.skill_ontology import (
    OntologyNameCollisionError,
    SkillNotFoundError,
    create_skill,
    create_skill_alias,
    resolve_skill,
)
from app.utils.skill_name import InvalidSkillNameError, normalize_skill_name


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (" Python ", "python"),
        ("Node-JS", "node js"),
        ("Node_JS", "node js"),
        ("C++", "c++"),
        ("C#", "c#"),
        (".NET", ".net"),
        ("CI/CD", "ci/cd"),
        ("ＡＰＩ\tTest", "api test"),
    ],
)
def test_normalize_skill_name(value: str, expected: str) -> None:
    assert normalize_skill_name(value) == expected


@pytest.mark.parametrize("value", ["", " \t ", 42])
def test_normalize_skill_name_rejects_empty_or_non_string(value: object) -> None:
    with pytest.raises(InvalidSkillNameError):
        normalize_skill_name(value)  # type: ignore[arg-type]


def test_skill_models_have_required_constraints_and_relationships() -> None:
    assert any(
        isinstance(constraint, UniqueConstraint)
        and tuple(column.name for column in constraint.columns) == ("normalized_name",)
        for constraint in Skill.__table__.constraints
    )
    assert "candidate_id" not in Skill.__table__.c
    assert "aliases" not in Skill.__table__.c
    assert Skill.__table__.c.deprecated.default is not None
    assert SkillAlias.skill.property.mapper.class_ is Skill
    assert EvidenceSkillLink.skill.property.mapper.class_ is Skill


def test_skill_alias_and_link_models_have_required_constraints() -> None:
    assert {
        foreign_key.target_fullname for foreign_key in SkillAlias.__table__.c.skill_id.foreign_keys
    } == {"skills.id"}
    assert any(
        isinstance(constraint, UniqueConstraint)
        and tuple(column.name for column in constraint.columns) == ("normalized_alias",)
        for constraint in SkillAlias.__table__.constraints
    )
    assert "updated_at" not in SkillAlias.__table__.c
    assert {
        foreign_key.target_fullname
        for foreign_key in EvidenceSkillLink.__table__.c.candidate_id.foreign_keys
    } == {"candidate_profiles.id"}
    assert {
        foreign_key.target_fullname
        for foreign_key in EvidenceSkillLink.__table__.c.evidence_unit_id.foreign_keys
    } == {"evidence_units.id"}
    assert any(
        isinstance(constraint, UniqueConstraint)
        and tuple(column.name for column in constraint.columns)
        == ("evidence_unit_id", "skill_id", "extraction_method", "extraction_version")
        for constraint in EvidenceSkillLink.__table__.constraints
    )
    assert {
        constraint.name
        for constraint in EvidenceSkillLink.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    } >= {
        "ck_evidence_skill_links_extraction_method",
        "ck_evidence_skill_links_extraction_confidence",
    }
    assert EvidenceSkillLink.__table__.c.context.type.__class__.__name__ == "JSONB"
    assert "passport_id" not in EvidenceSkillLink.__table__.c


def test_migration_has_current_head_and_correct_downgrade_order() -> None:
    source = (
        Path(__file__).parents[1] / "alembic" / "versions" / "20260718_0011_skill_ontology.py"
    ).read_text(encoding="utf-8")
    assert 'down_revision: Union[str, None] = "20260718_0010"' in source
    assert (
        source.index('op.drop_table("evidence_skill_links")')
        < source.index('op.drop_table("skill_aliases")')
        < source.index('op.drop_table("skills")')
    )


def test_resolve_skill_prefers_canonical_then_alias_and_is_read_only() -> None:
    canonical = Skill(
        id=uuid4(),
        canonical_name="Python",
        normalized_name="python",
        category="language",
        ontology_version="v1",
    )
    alias_skill = Skill(
        id=uuid4(),
        canonical_name="JavaScript",
        normalized_name="javascript",
        category="language",
        ontology_version="v1",
    )
    session = Mock()
    canonical_result = Mock()
    canonical_result.scalar_one_or_none.return_value = canonical
    alias_result = Mock()
    alias_result.scalar_one_or_none.return_value = alias_skill
    session.execute.side_effect = [canonical_result, alias_result]

    assert resolve_skill(session, " Python ") is canonical
    assert session.execute.call_count == 1
    session.add.assert_not_called()
    session.flush.assert_not_called()
    session.commit.assert_not_called()
    session.rollback.assert_not_called()


def test_resolve_skill_returns_alias_or_none() -> None:
    alias_skill = Skill(
        id=uuid4(),
        canonical_name="JavaScript",
        normalized_name="javascript",
        category="language",
        ontology_version="v1",
    )
    session = Mock()
    first = Mock()
    first.scalar_one_or_none.return_value = None
    second = Mock()
    second.scalar_one_or_none.return_value = alias_skill
    session.execute.side_effect = [first, second]
    assert resolve_skill(session, "JS") is alias_skill

    unknown_session = Mock()
    result = Mock()
    result.scalar_one_or_none.return_value = None
    unknown_session.execute.side_effect = [result, result]
    assert resolve_skill(unknown_session, "Unknown") is None


def test_ontology_write_creates_skill_and_alias_without_transaction_control() -> None:
    session = Mock()
    available = Mock()
    available.scalar_one_or_none.return_value = None
    session.execute.side_effect = [available, available]

    skill = create_skill(
        session,
        canonical_name="Node-JS",
        category="framework",
        description=None,
        ontology_version="v1",
    )

    assert skill.normalized_name == "node js"
    session.add.assert_called_once_with(skill)
    session.flush.assert_called_once()
    session.commit.assert_not_called()
    session.rollback.assert_not_called()


def test_ontology_write_rejects_collisions_and_missing_skill() -> None:
    session = Mock()
    existing = Mock()
    existing.scalar_one_or_none.return_value = uuid4()
    session.execute.return_value = existing
    with pytest.raises(OntologyNameCollisionError):
        create_skill(
            session,
            canonical_name="Python",
            category="language",
            description=None,
            ontology_version="v1",
        )

    missing = Mock()
    missing_result = Mock()
    missing_result.scalar_one_or_none.return_value = None
    missing.execute.return_value = missing_result
    with pytest.raises(SkillNotFoundError):
        create_skill_alias(missing, skill_id=uuid4(), alias="Py")


def test_ontology_write_rejects_skill_alias_cross_space_collisions() -> None:
    skill = make_skill()

    skill_vs_alias = Mock()
    no_skill = Mock()
    no_skill.scalar_one_or_none.return_value = None
    existing_alias = Mock()
    existing_alias.scalar_one_or_none.return_value = uuid4()
    skill_vs_alias.execute.side_effect = [no_skill, existing_alias]
    with pytest.raises(OntologyNameCollisionError):
        create_skill(
            skill_vs_alias,
            canonical_name="Py",
            category="language",
            description=None,
            ontology_version="v1",
        )

    alias_vs_skill = Mock()
    found_skill = Mock()
    found_skill.scalar_one_or_none.return_value = skill
    existing_skill = Mock()
    existing_skill.scalar_one_or_none.return_value = skill.id
    alias_vs_skill.execute.side_effect = [found_skill, existing_skill]
    with pytest.raises(OntologyNameCollisionError):
        create_skill_alias(alias_vs_skill, skill_id=skill.id, alias="Python")

    alias_vs_alias = Mock()
    existing_alias_id = Mock()
    existing_alias_id.scalar_one_or_none.return_value = uuid4()
    alias_vs_alias.execute.side_effect = [found_skill, no_skill, existing_alias_id]
    with pytest.raises(OntologyNameCollisionError):
        create_skill_alias(alias_vs_alias, skill_id=skill.id, alias="Py")


def make_evidence() -> EvidenceUnit:
    return EvidenceUnit(id=uuid4(), candidate_id=uuid4(), source_type="github_repository")


def make_skill() -> Skill:
    return Skill(
        id=uuid4(),
        canonical_name="Python",
        normalized_name="python",
        category="language",
        ontology_version="v1",
    )


def make_link_session(existing: EvidenceSkillLink | None) -> Mock:
    session = Mock()
    result = Mock()
    result.scalar_one_or_none.return_value = existing
    session.execute.return_value = result
    return session


def test_persist_evidence_skill_link_create_idempotency_and_update() -> None:
    evidence = make_evidence()
    skill = make_skill()
    context = {"signal": "language", "nested": {"value": "python"}}
    session = make_link_session(None)
    result = persist_evidence_skill_link(
        session,
        candidate_id=evidence.candidate_id,
        evidence_unit=evidence,
        skill=skill,
        extraction_method="deterministic",
        extraction_version=" v1 ",
        extraction_confidence=Decimal("1.00"),
        context=context,
    )
    assert (result.created, result.changed) == (True, True)
    assert result.link.extraction_version == "v1"
    assert result.link.context == context
    assert result.link.context is not context
    session.add.assert_called_once_with(result.link)
    session.flush.assert_called_once()

    existing = result.link
    unchanged_session = make_link_session(existing)
    unchanged = persist_evidence_skill_link(
        unchanged_session,
        candidate_id=evidence.candidate_id,
        evidence_unit=evidence,
        skill=skill,
        extraction_method="deterministic",
        extraction_version="v1",
        extraction_confidence=Decimal("1.00"),
        context=context,
    )
    assert (unchanged.created, unchanged.changed) == (False, False)
    unchanged_session.flush.assert_not_called()

    changed_session = make_link_session(existing)
    changed = persist_evidence_skill_link(
        changed_session,
        candidate_id=evidence.candidate_id,
        evidence_unit=evidence,
        skill=skill,
        extraction_method="deterministic",
        extraction_version="v1",
        extraction_confidence=Decimal("1.00"),
        context={"signal": "manifest"},
    )
    assert changed.link is existing
    assert (changed.created, changed.changed) == (False, True)
    changed_session.flush.assert_called_once()


@pytest.mark.parametrize(
    ("method", "confidence"),
    [("manual", Decimal("1.00")), ("ai", Decimal("0.75"))],
)
def test_persist_evidence_skill_link_creates_permitted_method(
    method: str, confidence: Decimal
) -> None:
    evidence = make_evidence()
    session = make_link_session(None)

    result = persist_evidence_skill_link(
        session,
        candidate_id=evidence.candidate_id,
        evidence_unit=evidence,
        skill=make_skill(),
        extraction_method=method,
        extraction_version="v1",
        extraction_confidence=confidence,
        context={"signal": "manual"},
    )

    assert result.link.extraction_method == method
    assert result.link.extraction_confidence == confidence


def test_persist_evidence_skill_link_supports_distinct_evidence_and_skill_identities() -> None:
    evidence = make_evidence()
    first_skill = make_skill()
    second_skill = make_skill()
    first = persist_evidence_skill_link(
        make_link_session(None),
        candidate_id=evidence.candidate_id,
        evidence_unit=evidence,
        skill=first_skill,
        extraction_method="deterministic",
        extraction_version="v1",
        extraction_confidence=Decimal("1.00"),
        context={},
    )
    second = persist_evidence_skill_link(
        make_link_session(None),
        candidate_id=evidence.candidate_id,
        evidence_unit=evidence,
        skill=second_skill,
        extraction_method="deterministic",
        extraction_version="v1",
        extraction_confidence=Decimal("1.00"),
        context={},
    )
    other_evidence = make_evidence()
    third = persist_evidence_skill_link(
        make_link_session(None),
        candidate_id=other_evidence.candidate_id,
        evidence_unit=other_evidence,
        skill=first_skill,
        extraction_method="deterministic",
        extraction_version="v1",
        extraction_confidence=Decimal("1.00"),
        context={},
    )

    assert first.link.skill_id != second.link.skill_id
    assert first.link.evidence_unit_id != third.link.evidence_unit_id


@pytest.mark.parametrize(
    ("method", "version", "confidence", "context", "error"),
    [
        ("invalid", "v1", Decimal("1.00"), {}, InvalidExtractionMethodError),
        ("ai", " ", Decimal("0.50"), {}, InvalidExtractionVersionError),
        ("ai", "v1", Decimal("-0.01"), {}, InvalidExtractionConfidenceError),
        ("ai", "v1", Decimal("1.01"), {}, InvalidExtractionConfidenceError),
        ("deterministic", "v1", Decimal("0.50"), {}, InvalidExtractionConfidenceError),
        ("ai", "v1", Decimal("0.50"), [], InvalidExtractionContextError),
    ],
)
def test_persist_evidence_skill_link_validates_input(
    method: str, version: str, confidence: Decimal, context: object, error: type[Exception]
) -> None:
    evidence = make_evidence()
    session = make_link_session(None)
    with pytest.raises(error):
        persist_evidence_skill_link(
            session,
            candidate_id=evidence.candidate_id,
            evidence_unit=evidence,
            skill=make_skill(),
            extraction_method=method,
            extraction_version=version,
            extraction_confidence=confidence,
            context=context,  # type: ignore[arg-type]
        )
    session.add.assert_not_called()
    session.flush.assert_not_called()


def test_persist_evidence_skill_link_rejects_candidate_mismatch_and_propagates_integrity_error() -> (
    None
):
    evidence = make_evidence()
    session = make_link_session(None)
    with pytest.raises(EvidenceSkillLinkCandidateMismatchError):
        persist_evidence_skill_link(
            session,
            candidate_id=uuid4(),
            evidence_unit=evidence,
            skill=make_skill(),
            extraction_method="manual",
            extraction_version="v1",
            extraction_confidence=Decimal("1.00"),
            context={},
        )
    session.add.assert_not_called()

    failing_session = make_link_session(None)
    failing_session.flush.side_effect = IntegrityError("insert", {}, Exception("unique violation"))
    with pytest.raises(IntegrityError):
        persist_evidence_skill_link(
            failing_session,
            candidate_id=evidence.candidate_id,
            evidence_unit=evidence,
            skill=make_skill(),
            extraction_method="ai",
            extraction_version="v2",
            extraction_confidence=Decimal("0.75"),
            context={},
        )
    failing_session.commit.assert_not_called()
    failing_session.rollback.assert_not_called()
