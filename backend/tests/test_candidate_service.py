from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.models.candidate_profile import CandidateProfile
from app.services.candidate import (
    MissingCandidateProfileFullNameError,
    patch_candidate_profile,
)


def make_profile(user_id: object | None = None) -> CandidateProfile:
    return CandidateProfile(
        id=uuid4(),
        user_id=user_id or uuid4(),
        full_name="Alan Yerkin",
        headline="Existing headline",
        desired_role="junior_python_backend_developer",
    )


def test_patch_creates_profile_with_database_default(monkeypatch: pytest.MonkeyPatch) -> None:
    session = Mock()
    user_id = uuid4()
    monkeypatch.setattr("app.services.candidate.get_candidate_profile", lambda *_args: None)
    session.refresh.side_effect = lambda profile: setattr(
        profile, "desired_role", "junior_python_backend_developer"
    )

    profile = patch_candidate_profile(session, user_id, {"full_name": "Alan Yerkin"})

    created = session.add.call_args.args[0]
    assert created.user_id == user_id
    assert profile.desired_role == "junior_python_backend_developer"
    session.commit.assert_called_once()
    session.refresh.assert_called_once_with(profile)


def test_patch_updates_only_explicit_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    session = Mock()
    profile = make_profile()
    monkeypatch.setattr("app.services.candidate.get_candidate_profile", lambda *_args: profile)

    result = patch_candidate_profile(session, profile.user_id, {"headline": None})

    assert result is profile
    assert profile.headline is None
    assert profile.full_name == "Alan Yerkin"
    session.add.assert_not_called()


def test_patch_missing_profile_requires_full_name(monkeypatch: pytest.MonkeyPatch) -> None:
    session = Mock()
    monkeypatch.setattr("app.services.candidate.get_candidate_profile", lambda *_args: None)

    with pytest.raises(MissingCandidateProfileFullNameError):
        patch_candidate_profile(session, uuid4(), {})

    session.add.assert_not_called()
    session.commit.assert_not_called()


def test_patch_rolls_back_database_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    session = Mock()
    profile = make_profile()
    monkeypatch.setattr("app.services.candidate.get_candidate_profile", lambda *_args: profile)
    session.commit.side_effect = SQLAlchemyError("database error")

    with pytest.raises(SQLAlchemyError):
        patch_candidate_profile(session, profile.user_id, {"bio": "Updated"})

    session.rollback.assert_called_once()
    session.refresh.assert_not_called()
