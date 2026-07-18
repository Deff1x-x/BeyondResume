from inspect import getsource
from unittest.mock import Mock, call
from uuid import UUID, uuid4

import pytest

from app.models.evidence_skill_link import EvidenceSkillLink
from app.models.evidence_unit import EvidenceUnit
from app.services.evidence_skill_links import EvidenceSkillLinkPersistenceResult
from app.services.github_evidence_commands import (
    GITHUB_DETERMINISTIC_EXTRACTION_METHOD,
    GITHUB_DETERMINISTIC_EXTRACTION_VERSION,
)
from app.services.github_evidence_skill_link_orchestration import (
    GitHubEvidenceSkillLinkOrchestrationResult,
)
from app.services.github_skill_link_reconciliation import (
    reconcile_github_evidence_skill_links,
)
import app.services.github_skill_link_reconciliation as reconciliation_module


def make_evidence_unit(evidence_unit_id: UUID, candidate_id: UUID) -> EvidenceUnit:
    return EvidenceUnit(
        id=evidence_unit_id,
        candidate_id=candidate_id,
        source_type="github_repository",
    )


def make_link(
    *,
    candidate_id: UUID,
    evidence_unit_id: UUID,
    skill_id: UUID,
    extraction_method: str = GITHUB_DETERMINISTIC_EXTRACTION_METHOD,
    extraction_version: str = GITHUB_DETERMINISTIC_EXTRACTION_VERSION,
) -> EvidenceSkillLink:
    return EvidenceSkillLink(
        candidate_id=candidate_id,
        evidence_unit_id=evidence_unit_id,
        skill_id=skill_id,
        extraction_method=extraction_method,
        extraction_version=extraction_version,
    )


def persistence_result(
    link: EvidenceSkillLink, *, created: bool, changed: bool
) -> EvidenceSkillLinkPersistenceResult:
    return EvidenceSkillLinkPersistenceResult(link=link, created=created, changed=changed)


def mock_existing_links(session: Mock, links: tuple[EvidenceSkillLink, ...]) -> None:
    scalar_result = Mock()
    scalar_result.all.return_value = links
    execution_result = Mock()
    execution_result.scalars.return_value = scalar_result
    session.execute.return_value = execution_result


def test_reconciliation_calls_orchestration_once_and_removes_only_stale_link(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate_id = uuid4()
    evidence_unit = make_evidence_unit(uuid4(), candidate_id)
    desired = make_link(
        candidate_id=candidate_id,
        evidence_unit_id=evidence_unit.id,
        skill_id=UUID("00000000-0000-0000-0000-000000000002"),
    )
    stale = make_link(
        candidate_id=candidate_id,
        evidence_unit_id=evidence_unit.id,
        skill_id=UUID("00000000-0000-0000-0000-000000000001"),
    )
    session = Mock()
    mock_existing_links(session, (stale, desired))
    orchestration = Mock(
        return_value=GitHubEvidenceSkillLinkOrchestrationResult(
            persistence_results=(persistence_result(desired, created=True, changed=True),)
        )
    )
    monkeypatch.setattr(
        reconciliation_module, "persist_resolved_github_skill_candidates", orchestration
    )

    result = reconcile_github_evidence_skill_links(
        session,
        candidate_id=candidate_id,
        evidence_unit=evidence_unit,
        resolved_candidates=(),
    )

    orchestration.assert_called_once_with(
        session,
        candidate_id=candidate_id,
        evidence_unit=evidence_unit,
        resolved_candidates=(),
    )
    session.delete.assert_called_once_with(stale)
    assert result.links == (desired,)
    assert (result.created_count, result.changed_count, result.unchanged_count) == (1, 0, 0)
    assert result.removed_count == 1


def test_existing_link_query_uses_exact_strict_scope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate_id = uuid4()
    evidence_unit = make_evidence_unit(uuid4(), candidate_id)
    session = Mock()
    mock_existing_links(session, ())
    monkeypatch.setattr(
        reconciliation_module,
        "persist_resolved_github_skill_candidates",
        Mock(return_value=GitHubEvidenceSkillLinkOrchestrationResult(persistence_results=())),
    )

    reconcile_github_evidence_skill_links(
        session,
        candidate_id=candidate_id,
        evidence_unit=evidence_unit,
        resolved_candidates=(),
    )

    statement = session.execute.call_args.args[0]
    assert set(statement.compile().params.values()) == {
        candidate_id,
        evidence_unit.id,
        GITHUB_DETERMINISTIC_EXTRACTION_METHOD,
        GITHUB_DETERMINISTIC_EXTRACTION_VERSION,
    }


def test_empty_desired_set_deletes_every_scoped_link_in_skill_id_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate_id = uuid4()
    evidence_unit = make_evidence_unit(uuid4(), candidate_id)
    later = make_link(
        candidate_id=candidate_id,
        evidence_unit_id=evidence_unit.id,
        skill_id=UUID("00000000-0000-0000-0000-000000000002"),
    )
    earlier = make_link(
        candidate_id=candidate_id,
        evidence_unit_id=evidence_unit.id,
        skill_id=UUID("00000000-0000-0000-0000-000000000001"),
    )
    session = Mock()
    mock_existing_links(session, (later, earlier))
    monkeypatch.setattr(
        reconciliation_module,
        "persist_resolved_github_skill_candidates",
        Mock(return_value=GitHubEvidenceSkillLinkOrchestrationResult(persistence_results=())),
    )

    result = reconcile_github_evidence_skill_links(
        session,
        candidate_id=candidate_id,
        evidence_unit=evidence_unit,
        resolved_candidates=(),
    )

    assert session.delete.call_args_list == [call(earlier), call(later)]
    assert result.links == ()
    assert result.removed_count == 2


def test_reconciliation_copies_persistence_outcomes_without_recounting_links(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate_id = uuid4()
    evidence_unit = make_evidence_unit(uuid4(), candidate_id)
    created_link = make_link(
        candidate_id=candidate_id, evidence_unit_id=evidence_unit.id, skill_id=uuid4()
    )
    changed_link = make_link(
        candidate_id=candidate_id, evidence_unit_id=evidence_unit.id, skill_id=uuid4()
    )
    unchanged_link = make_link(
        candidate_id=candidate_id, evidence_unit_id=evidence_unit.id, skill_id=uuid4()
    )
    session = Mock()
    mock_existing_links(session, (created_link, changed_link, unchanged_link))
    monkeypatch.setattr(
        reconciliation_module,
        "persist_resolved_github_skill_candidates",
        Mock(
            return_value=GitHubEvidenceSkillLinkOrchestrationResult(
                persistence_results=(
                    persistence_result(created_link, created=True, changed=True),
                    persistence_result(changed_link, created=False, changed=True),
                    persistence_result(unchanged_link, created=False, changed=False),
                )
            )
        ),
    )

    result = reconcile_github_evidence_skill_links(
        session,
        candidate_id=candidate_id,
        evidence_unit=evidence_unit,
        resolved_candidates=(),
    )

    assert result.links == (created_link, changed_link, unchanged_link)
    assert (result.created_count, result.changed_count, result.unchanged_count) == (1, 1, 1)
    assert result.removed_count == 0
    session.delete.assert_not_called()


def test_orchestration_error_propagates_without_stale_delete_or_transaction_control(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate_id = uuid4()
    evidence_unit = make_evidence_unit(uuid4(), candidate_id)
    session = Mock()
    mock_existing_links(session, ())
    error = RuntimeError("orchestration failed")
    monkeypatch.setattr(
        reconciliation_module,
        "persist_resolved_github_skill_candidates",
        Mock(side_effect=error),
    )

    with pytest.raises(RuntimeError, match="orchestration failed") as raised:
        reconcile_github_evidence_skill_links(
            session,
            candidate_id=candidate_id,
            evidence_unit=evidence_unit,
            resolved_candidates=(),
        )

    assert raised.value is error
    session.delete.assert_not_called()
    session.commit.assert_not_called()
    session.rollback.assert_not_called()
    session.flush.assert_not_called()


def test_reconciliation_has_no_direct_pipeline_or_transaction_implementation() -> None:
    source = getsource(reconciliation_module)

    assert "build_github_evidence_commands" not in source
    assert "build_github_skill_link_values" not in source
    assert "persist_github_evidence_skill_link" not in source
    assert ".commit(" not in source
    assert ".rollback(" not in source
    assert ".flush(" not in source
    assert "MappingProxyType" not in source
    assert "deep_thaw" not in source
