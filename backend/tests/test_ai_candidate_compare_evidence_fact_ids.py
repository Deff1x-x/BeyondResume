"""Opaque evidence fact_id stability and privacy tests."""

from __future__ import annotations

from copy import deepcopy
from uuid import UUID

import pytest

from app.schemas.employer import (
    MatchDetailsCandidateResponse,
    MatchDetailsEvidenceResponse,
    MatchDetailsMatchResponse,
    MatchDetailsPassportResponse,
    MatchDetailsResponse,
    MatchSkillGroupResponse,
)
from app.services import ai_candidate_compare as service


CANDIDATE_ID = UUID("11111111-1111-1111-1111-111111111111")
OTHER_CANDIDATE_ID = UUID("22222222-2222-2222-2222-222222222222")


def _evidence(
    *,
    title: str | None = "Backend API ownership",
    source_type: str = "github",
    skills: list[str] | None = None,
    verification_status: str | None = "verified",
    ownership_status: str | None = "owned",
) -> MatchDetailsEvidenceResponse:
    return MatchDetailsEvidenceResponse(
        source_type=source_type,
        title=title,
        verification_status=verification_status,
        ownership_status=ownership_status,
        skills=skills if skills is not None else ["Python", "FastAPI"],
    )


def _details_with_evidence(
    evidence: list[MatchDetailsEvidenceResponse],
) -> MatchDetailsResponse:
    return MatchDetailsResponse(
        candidate=MatchDetailsCandidateResponse(
            id=CANDIDATE_ID, name="Hidden Name", headline=None, avatar=None
        ),
        match=MatchDetailsMatchResponse(
            score=80,
            required=MatchSkillGroupResponse(matched=["Python"], missing=[]),
            preferred=MatchSkillGroupResponse(matched=[], missing=[]),
        ),
        passport=MatchDetailsPassportResponse(top_skills=["Python"], skills=[]),
        evidence=evidence,
        roadmap=[],
    )


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    service.clear_ai_candidate_compare_cache()


def test_evidence_fact_id_excludes_title_and_pii_like_text() -> None:
    title = "Acme Corp — owned by Jane Doe (jane.doe@example.com)"
    fact_id = service._evidence_fact_id(
        candidate_id=CANDIDATE_ID, evidence=_evidence(title=title)
    )
    assert fact_id.startswith(f"candidate:{CANDIDATE_ID}:evidence:")
    suffix = fact_id.rsplit(":", 1)[-1]
    assert len(suffix) == service.EVIDENCE_FACT_HASH_PREFIX_LENGTH
    assert suffix.isalnum()
    assert "acme" not in fact_id.casefold()
    assert "jane" not in fact_id.casefold()
    assert "doe" not in fact_id.casefold()
    assert "example.com" not in fact_id.casefold()
    assert "@" not in fact_id
    assert title not in fact_id
    assert "Backend" not in fact_id
    assert "API" not in fact_id


def test_identical_evidence_content_yields_identical_fact_id() -> None:
    first = service._evidence_fact_id(candidate_id=CANDIDATE_ID, evidence=_evidence())
    second = service._evidence_fact_id(candidate_id=CANDIDATE_ID, evidence=_evidence())
    assert first == second


def test_meaningful_evidence_change_changes_fact_id() -> None:
    base = service._evidence_fact_id(candidate_id=CANDIDATE_ID, evidence=_evidence())
    changed_title = service._evidence_fact_id(
        candidate_id=CANDIDATE_ID,
        evidence=_evidence(title="Different project ownership summary"),
    )
    changed_skills = service._evidence_fact_id(
        candidate_id=CANDIDATE_ID,
        evidence=_evidence(skills=["Python", "PostgreSQL"]),
    )
    assert base != changed_title
    assert base != changed_skills


def test_skill_order_does_not_change_evidence_fact_id() -> None:
    left = service._evidence_fact_id(
        candidate_id=CANDIDATE_ID,
        evidence=_evidence(skills=["FastAPI", "Python", "Docker"]),
    )
    right = service._evidence_fact_id(
        candidate_id=CANDIDATE_ID,
        evidence=_evidence(skills=["Docker", "Python", "FastAPI"]),
    )
    assert left == right


def test_evidence_fact_id_stable_across_candidate_payload_builds() -> None:
    details = _details_with_evidence([_evidence(title="Stable evidence title")])
    first_payload, first_facts = service._candidate_payload(
        candidate_id=CANDIDATE_ID, label="Candidate A", details=details
    )
    second_payload, second_facts = service._candidate_payload(
        candidate_id=CANDIDATE_ID, label="Candidate A", details=details
    )
    first_ids = [
        item["fact_id"]
        for item in first_payload["evidence_summaries"]  # type: ignore[index]
    ]
    second_ids = [
        item["fact_id"]
        for item in second_payload["evidence_summaries"]  # type: ignore[index]
    ]
    assert first_ids == second_ids
    assert first_ids
    for fact_id in first_ids:
        assert isinstance(fact_id, str)
        assert "Stable evidence title" not in fact_id
        assert fact_id in first_facts
        assert fact_id in second_facts


def test_semantic_grounding_accepts_opaque_evidence_fact_refs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.schemas.ai_candidate_compare import AiCandidateCompareLlmPayload

    left = CANDIDATE_ID
    right = OTHER_CANDIDATE_ID
    evidence_fact = service._evidence_fact_id(
        candidate_id=left, evidence=_evidence(title="Must not appear in id")
    )
    facts = {
        f"candidate:{left}:match-score": {"type": "match_score", "score": 80},
        f"candidate:{right}:match-score": {"type": "match_score", "score": 60},
        evidence_fact: {"type": "evidence_summary"},
    }
    context = service.AiCandidateCompareContext(
        vacancy_id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        candidate_ids=(left, right),
        payload={"candidates": [], "facts": facts},
        fact_ids=frozenset(facts),
        generation_mode="mock",
    )
    payload = {
        "summary": "Candidate A has employer-safe evidence supporting required coverage.",
        "candidate_assessments": [
            {
                "candidate_id": str(left),
                "strengths": [
                    {
                        "text": "Evidence summary supports required skill coverage.",
                        "fact_refs": [evidence_fact],
                    }
                ],
                "risks": [
                    {
                        "text": "Match score remains advisory.",
                        "fact_refs": [f"candidate:{left}:match-score"],
                    }
                ],
            },
            {
                "candidate_id": str(right),
                "strengths": [
                    {
                        "text": "Match score is available.",
                        "fact_refs": [f"candidate:{right}:match-score"],
                    }
                ],
                "risks": [
                    {
                        "text": "Weaker evidence depth in supplied facts.",
                        "fact_refs": [f"candidate:{right}:match-score"],
                    }
                ],
            },
        ],
        "key_differences": [
            {
                "text": "Evidence availability differs.",
                "fact_refs": [evidence_fact, f"candidate:{right}:match-score"],
            }
        ],
        "interview_focus_questions": [
            {
                "question": "Walk through the production service behind this evidence.",
                "candidate_ids": [str(left)],
                "fact_refs": [evidence_fact],
            }
        ],
        "recommended_candidate_id": None,
        "recommendation_rationale": None,
        "confidence": "low",
        "uncertainties": [
            {
                "text": "Evidence depth remains limited to summaries.",
                "fact_refs": [evidence_fact],
            }
        ],
    }

    class Provider:
        def generate(self, prompt: str) -> str:
            return AiCandidateCompareLlmPayload.model_validate(payload).model_dump_json()

    monkeypatch.setattr(service, "get_ai_candidate_compare_provider", lambda: Provider())
    result = service.get_ai_candidate_compare(context)
    assert result.candidate_assessments[0].strengths[0].fact_refs == [evidence_fact]
    assert "Must not appear" not in result.model_dump_json()


def test_cache_identity_changes_when_evidence_content_changes() -> None:
    vacancy_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    left = CANDIDATE_ID
    right = OTHER_CANDIDATE_ID
    evidence_a = _evidence(title="Service ownership summary A")
    evidence_b = _evidence(title="Service ownership summary B")
    fact_a = service._evidence_fact_id(candidate_id=left, evidence=evidence_a)
    fact_b = service._evidence_fact_id(candidate_id=left, evidence=evidence_b)
    assert fact_a != fact_b

    base_payload = {
        "candidates": [{"candidate_id": str(left)}, {"candidate_id": str(right)}],
        "facts": {fact_a: {"type": "evidence_summary", "title": evidence_a.title}},
    }
    changed_payload = deepcopy(base_payload)
    changed_payload["facts"] = {fact_b: {"type": "evidence_summary", "title": evidence_b.title}}

    context_a = service.AiCandidateCompareContext(
        vacancy_id=vacancy_id,
        candidate_ids=(left, right),
        payload=base_payload,
        fact_ids=frozenset(base_payload["facts"]),
        generation_mode="live",
    )
    context_b = service.AiCandidateCompareContext(
        vacancy_id=vacancy_id,
        candidate_ids=(left, right),
        payload=changed_payload,
        fact_ids=frozenset(changed_payload["facts"]),
        generation_mode="live",
    )
    assert service._cache_key(context_a) != service._cache_key(context_b)
