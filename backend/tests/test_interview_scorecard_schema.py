"""Schema validation for Interview Scorecard."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.interview_scorecard import (
    InterviewScorecardResponse,
    InterviewScorecardSummary,
    InterviewScorecardUpsertRequest,
)


def _valid_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "status": "completed",
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
    assert body.status == "completed"
    assert body.technical_competency == 4
    assert body.recommendation == "yes"


def test_status_defaults_to_draft() -> None:
    payload = _valid_payload()
    del payload["status"]
    body = InterviewScorecardUpsertRequest.model_validate(payload)
    assert body.status == "draft"


def test_draft_allows_missing_ratings_and_recommendation() -> None:
    body = InterviewScorecardUpsertRequest.model_validate(
        {
            "status": "draft",
            "technical_competency": 4,
        }
    )
    assert body.status == "draft"
    assert body.technical_competency == 4
    assert body.experience_relevance is None
    assert body.communication is None
    assert body.ownership is None
    assert body.recommendation is None


def test_empty_draft_allowed() -> None:
    body = InterviewScorecardUpsertRequest.model_validate({"status": "draft"})
    assert body.status == "draft"
    assert body.technical_competency is None
    assert body.recommendation is None


def test_all_four_scores_required_when_completed() -> None:
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


def test_recommendation_required_when_completed() -> None:
    payload = _valid_payload()
    del payload["recommendation"]
    with pytest.raises(ValidationError):
        InterviewScorecardUpsertRequest.model_validate(payload)


def test_completed_with_null_rating_rejected() -> None:
    with pytest.raises(ValidationError):
        InterviewScorecardUpsertRequest.model_validate(
            _valid_payload(communication=None)
        )


def test_invalid_status_rejected() -> None:
    with pytest.raises(ValidationError):
        InterviewScorecardUpsertRequest.model_validate(_valid_payload(status="final"))


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
        status="completed",
        technical_competency=3,
        experience_relevance=3,
        communication=3,
        ownership=3,
        interview_summary=None,
        interview_notes=None,
        recommendation="mixed",
        summary=InterviewScorecardSummary(
            status="completed",
            completed_criteria_count=4,
            total_criteria_count=4,
            average_rating=3.0,
            strongest_dimensions=[
                "Technical Competency",
                "Experience Relevance",
                "Communication",
                "Ownership",
            ],
            weakest_dimensions=[
                "Technical Competency",
                "Experience Relevance",
                "Communication",
                "Ownership",
            ],
            unanswered_dimensions=[],
            recommendation="mixed",
        ),
        created_at=now,
        updated_at=now,
    )
    dumped = response.model_dump()
    assert "employer_id" not in dumped
    assert dumped["status"] == "completed"
    assert dumped["summary"]["completed_criteria_count"] == 4
    assert dumped["summary"]["average_rating"] == 3.0


def test_response_summary_defaults_for_draft() -> None:
    now = datetime.now(UTC)
    response = InterviewScorecardResponse(
        id=uuid4(),
        vacancy_id=uuid4(),
        candidate_id=uuid4(),
        status="draft",
        technical_competency=None,
        experience_relevance=None,
        communication=None,
        ownership=None,
        interview_summary=None,
        interview_notes=None,
        recommendation=None,
        summary=InterviewScorecardSummary(
            status="draft",
            completed_criteria_count=0,
            total_criteria_count=4,
            average_rating=None,
            strongest_dimensions=[],
            weakest_dimensions=[],
            unanswered_dimensions=[
                "Technical Competency",
                "Experience Relevance",
                "Communication",
                "Ownership",
            ],
            recommendation=None,
        ),
        created_at=now,
        updated_at=now,
    )
    dumped = response.model_dump()
    assert dumped["status"] == "draft"
    assert dumped["summary"]["average_rating"] is None
    assert dumped["summary"]["unanswered_dimensions"] == [
        "Technical Competency",
        "Experience Relevance",
        "Communication",
        "Ownership",
    ]
