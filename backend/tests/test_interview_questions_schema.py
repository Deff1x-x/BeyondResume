"""Schema and safety validation for AI Interview Questions."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.interview_questions import InterviewQuestion, InterviewQuestionsResponse
from app.services.interview_questions import (
    InterviewQuestionsUnavailableError,
    parse_interview_questions_response,
)


def _question(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "category": "technical",
        "question": "How have you used Python in production systems?",
        "reason": "Python is a matched required skill for this vacancy.",
        "target_skill": "Python",
        "evidence_basis": "Sources: github_repository",
    }
    payload.update(overrides)
    return payload


def test_valid_response_accepted() -> None:
    response = InterviewQuestionsResponse.model_validate(
        {
            "questions": [
                _question(),
                _question(question="Describe ownership of a delivery incident."),
            ]
        }
    )
    assert len(response.questions) == 2


def test_extra_field_rejected() -> None:
    with pytest.raises(ValidationError):
        InterviewQuestionsResponse.model_validate({"questions": [_question()], "verdict": "hire"})


def test_invalid_category_rejected() -> None:
    with pytest.raises(ValidationError):
        InterviewQuestion.model_validate(_question(category="behavioral"))


def test_blank_normalized_question_rejected() -> None:
    with pytest.raises(ValidationError):
        InterviewQuestion.model_validate(_question(question="   "))


def test_blank_normalized_reason_rejected() -> None:
    with pytest.raises(ValidationError):
        InterviewQuestion.model_validate(_question(reason="\n\t"))


def test_empty_optional_fields_become_null() -> None:
    item = InterviewQuestion.model_validate(_question(target_skill="  ", evidence_basis=""))
    assert item.target_skill is None
    assert item.evidence_basis is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("question", "q" * 281),
        ("reason", "r" * 401),
        ("target_skill", "s" * 81),
        ("evidence_basis", "e" * 201),
    ],
)
def test_oversized_fields_rejected(field: str, value: str) -> None:
    with pytest.raises(ValidationError):
        InterviewQuestion.model_validate(_question(**{field: value}))


def test_zero_questions_rejected() -> None:
    with pytest.raises(ValidationError):
        InterviewQuestionsResponse.model_validate({"questions": []})


def test_more_than_eight_rejected() -> None:
    with pytest.raises(ValidationError):
        InterviewQuestionsResponse.model_validate(
            {
                "questions": [
                    _question(question=f"Question number {index} about systems?")
                    for index in range(9)
                ]
            }
        )


def test_case_insensitive_duplicate_rejected() -> None:
    with pytest.raises(ValidationError):
        InterviewQuestionsResponse.model_validate(
            {
                "questions": [
                    _question(question="How have you used Python?"),
                    _question(question="how have you used python?"),
                ]
            }
        )


def test_whitespace_normalized_duplicate_rejected() -> None:
    with pytest.raises(ValidationError):
        InterviewQuestionsResponse.model_validate(
            {
                "questions": [
                    _question(question="How have you used Python?"),
                    _question(question="How   have you used   Python?"),
                ]
            }
        )


def test_distinct_questions_accepted() -> None:
    response = InterviewQuestionsResponse.model_validate(
        {
            "questions": [
                _question(question="How have you used Python?"),
                _question(
                    category="risk_validation",
                    question="How would you ramp up on Redis for this role?",
                    target_skill="Redis",
                    evidence_basis=None,
                ),
            ]
        }
    )
    assert len(response.questions) == 2


def test_safety_guard_rejects_age_question() -> None:
    payload = {
        "questions": [
            _question(
                question="How old are you and how does that affect your career plans?",
                reason="Unsafe question for coverage.",
            )
        ]
    }
    with pytest.raises(InterviewQuestionsUnavailableError):
        parse_interview_questions_response(
            InterviewQuestionsResponse.model_validate(payload).model_dump_json()
        )


@pytest.mark.parametrize(
    "question",
    [
        "What is your marital status?",
        "Do you have children that would affect travel?",
        "Are you pregnant or planning maternity leave?",
        "Do you have any medical diagnosis we should know?",
        "What are your religious beliefs?",
        "What are your political views?",
        "What is your racial background?",
        "What is your sexual orientation?",
    ],
)
def test_safety_guard_rejects_protected_trait_questions(question: str) -> None:
    payload = {
        "questions": [_question(question=question, reason="Coverage for protected-trait safety.")]
    }
    with pytest.raises(InterviewQuestionsUnavailableError):
        parse_interview_questions_response(
            InterviewQuestionsResponse.model_validate(payload).model_dump_json()
        )


def test_safety_guard_accepts_safe_technical_question() -> None:
    payload = {"questions": [_question()]}
    result = parse_interview_questions_response(
        InterviewQuestionsResponse.model_validate(payload).model_dump_json()
    )
    assert result.questions[0].category == "technical"


@pytest.mark.parametrize(
    "question",
    [
        "How would you diagnose a race condition in a concurrent API worker?",
        "What health check endpoint would you expose for this service?",
        "How do you organize a React component family for shared form state?",
        "When would you prefer a native application over a web client?",
    ],
)
def test_safety_guard_allows_technical_phrases(question: str) -> None:
    payload = {"questions": [_question(question=question, reason="Technical interview probe.")]}
    result = parse_interview_questions_response(
        InterviewQuestionsResponse.model_validate(payload).model_dump_json()
    )
    assert result.questions[0].question == question


@pytest.mark.parametrize(
    "question",
    [
        "How old are you?",
        "What is your marital status?",
        "Are you pregnant or planning a family?",
        "What are your religious beliefs?",
    ],
)
def test_safety_guard_rejects_obvious_protected_questions(question: str) -> None:
    payload = {
        "questions": [_question(question=question, reason="Coverage for protected-trait safety.")]
    }
    with pytest.raises(InterviewQuestionsUnavailableError) as error:
        parse_interview_questions_response(
            InterviewQuestionsResponse.model_validate(payload).model_dump_json()
        )
    assert question.casefold() not in str(error.value).casefold()
