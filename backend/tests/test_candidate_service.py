from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.models.candidate_profile import CandidateProfile, OnboardingStatus
from app.services.candidate import CandidateProfileNotFoundError, patch_candidate_profile


def make_profile(user_id: object | None = None) -> CandidateProfile:
    return CandidateProfile(
        id=uuid4(),
        user_id=user_id or uuid4(),
        display_name="Alan Yerkin",
        target_role="Junior developer",
        onboarding_status=OnboardingStatus.PROFILE_REQUIRED,
        remote_preference="remote",
    )


def test_patch_updates_only_explicit_fields_and_keeps_profile_required(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = Mock()
    profile = make_profile()
    monkeypatch.setattr("app.services.candidate.get_candidate_profile", lambda *_args: profile)

    result = patch_candidate_profile(session, profile.user_id, {"display_name": "Updated"})

    assert result is profile
    assert profile.display_name == "Updated"
    assert profile.target_role == "Junior developer"
    assert profile.onboarding_status is OnboardingStatus.PROFILE_REQUIRED
    session.commit.assert_called_once()


def test_patch_missing_profile_does_not_create_second_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = Mock()
    monkeypatch.setattr("app.services.candidate.get_candidate_profile", lambda *_args: None)

    with pytest.raises(CandidateProfileNotFoundError):
        patch_candidate_profile(session, uuid4(), {"display_name": "Alan"})

    session.add.assert_not_called()
    session.commit.assert_not_called()


def test_patch_rolls_back_database_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    session = Mock()
    profile = make_profile()
    monkeypatch.setattr("app.services.candidate.get_candidate_profile", lambda *_args: profile)
    session.commit.side_effect = SQLAlchemyError("database error")

    with pytest.raises(SQLAlchemyError):
        patch_candidate_profile(session, profile.user_id, {"summary": "Updated"})

    session.rollback.assert_called_once()


def test_explicit_null_differs_from_absent_field(monkeypatch: pytest.MonkeyPatch) -> None:
    session = Mock()
    profile = make_profile()
    profile.summary = "Existing"
    monkeypatch.setattr("app.services.candidate.get_candidate_profile", lambda *_args: profile)
    patch_candidate_profile(session, profile.user_id, {})
    assert profile.summary == "Existing"
    patch_candidate_profile(session, profile.user_id, {"summary": None})
    assert profile.summary is None


def test_patch_cannot_modify_another_candidates_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    session = Mock()
    first = make_profile()
    second = make_profile()
    monkeypatch.setattr(
        "app.services.candidate.get_candidate_profile",
        lambda _session, user_id: first if user_id == first.user_id else second,
    )
    patch_candidate_profile(session, first.user_id, {"display_name": "Updated"})
    assert first.display_name == "Updated"
    assert second.display_name == "Alan Yerkin"
