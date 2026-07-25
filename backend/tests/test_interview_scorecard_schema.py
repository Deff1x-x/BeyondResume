"""Schema validation for Interview Scorecard."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.interview_scorecard import (
    InterviewScorecardResponse,
    InterviewScorecardUpsertRequest,
)


def _valid_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "technical_competency": 4,
        "experience_relevance": 3,
        "communication": 5,
        "ownership": 4,
        "interview_summary": "Solid technical depth.",
        "interview_notes": "Asked about distributed systems.",
        "recommendation": "yes",
    }
    payload.update(overrides)
    return payload


def test_valid_request_accepted() -> None:
    body = InterviewScorecardUpsertRequest.model_validate(_valid_payload())
    assert body.technical_competency == 4
    assert body.recommendation == "yes"


def test_all_four_scores_required() -> None:
    for field in (
        "technical_competency",
        "experience_relevance",
        "communication",
        "ownership",
    ):
        payload = _valid_payload()
        del payload[field]
        with pytest.raises(ValidationError):
            InterviewScorecardUpsertRequest.model_validate(payload)


def test_recommendation_required() -> None:
    payload = _valid_payload()
    del payload["recommendation"]
    with pytest.raises(ValidationError):
        InterviewScorecardUpsertRequest.model_validate(payload)


def test_scores_one_and_five_accepted() -> None:
    body = InterviewScorecardUpsertRequest.model_validate(
        _valid_payload(
            technical_competency=1,
            experience_relevance=5,
            communication=1,
            ownership=5,
        )
    )
    assert body.technical_competency == 1
    assert body.experience_relevance == 5


@pytest.mark.parametrize("score", [0, 6])
def test_score_out_of_range_rejected(score: int) -> None:
    with pytest.raises(ValidationError):
        InterviewScorecardUpsertRequest.model_validate(_valid_payload(technical_competency=score))


def test_non_integer_score_rejected() -> None:
    with pytest.raises(ValidationError):
        InterviewScorecardUpsertRequest.model_validate(_valid_payload(technical_competency=3.5))


def test_invalid_recommendation_rejected() -> None:
    with pytest.raises(ValidationError):
        InterviewScorecardUpsertRequest.model_validate(_valid_payload(recommendation="strong_hire"))


def test_unknown_field_rejected() -> None:
    with pytest.raises(ValidationError):
        InterviewScorecardUpsertRequest.model_validate(_valid_payload(overall_score=4))


def test_summary_max_length() -> None:
    with pytest.raises(ValidationError):
        InterviewScorecardUpsertRequest.model_validate(_valid_payload(interview_summary="x" * 1201))
    body = InterviewScorecardUpsertRequest.model_validate(
        _valid_payload(interview_summary="x" * 1200)
    )
    assert body.interview_summary is not None
    assert len(body.interview_summary) == 1200


def test_notes_max_length() -> None:
    with pytest.raises(ValidationError):
        InterviewScorecardUpsertRequest.model_validate(_valid_payload(interview_notes="y" * 5001))
    body = InterviewScorecardUpsertRequest.model_validate(
        _valid_payload(interview_notes="y" * 5000)
    )
    assert body.interview_notes is not None
    assert len(body.interview_notes) == 5000


def test_whitespace_summary_becomes_null() -> None:
    body = InterviewScorecardUpsertRequest.model_validate(_valid_payload(interview_summary="   "))
    assert body.interview_summary is None


def test_whitespace_notes_become_null() -> None:
    body = InterviewScorecardUpsertRequest.model_validate(_valid_payload(interview_notes="\n\t  "))
    assert body.interview_notes is None


def test_bool_score_follows_project_coercion() -> None:
    """Project schemas use non-strict ints; bool coerces like other employer fields."""
    body = InterviewScorecardUpsertRequest.model_validate(_valid_payload(technical_competency=True))
    assert body.technical_competency == 1


def test_response_excludes_employer_id() -> None:
    now = datetime.now(UTC)
    response = InterviewScorecardResponse(
        id=uuid4(),
        vacancy_id=uuid4(),
        candidate_id=uuid4(),
        technical_competency=3,
        experience_relevance=3,
        communication=3,
        ownership=3,
        interview_summary=None,
        interview_notes=None,
        recommendation="mixed",
        created_at=now,
        updated_at=now,
    )
    assert "employer_id" not in response.model_dump()
