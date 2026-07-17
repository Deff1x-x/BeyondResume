from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.core.security import hash_password
from app.models.audit_event import AuditEvent
from app.models.candidate_profile import CandidateProfile
from app.models.user import User
from app.services.auth import (
    DuplicateEmailError,
    PasswordPolicyError,
    RegistrationPersistenceError,
    authenticate_user,
    register_user,
    validate_registration_password,
)


def make_user(role: str = "candidate", status: str = "active") -> User:
    return User(
        id=uuid4(),
        email="user@example.com",
        password_hash=hash_password("StrongPass123"),
        role=role,
        status=status,
    )


def test_candidate_registration_creates_profile_and_audit_event_atomically(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = Mock()
    monkeypatch.setattr("app.services.auth.get_user_by_email", lambda *_: None)
    registered = register_user(session, "user@example.com", "StrongPass123", "candidate")

    added = [call.args[0] for call in session.add.call_args_list]
    user = next(item for item in added if isinstance(item, User))
    profile = next(item for item in added if isinstance(item, CandidateProfile))
    audit_event = next(item for item in added if isinstance(item, AuditEvent))

    assert registered is user
    assert registered.status == "active"
    assert registered.password_hash != "StrongPass123"
    assert profile.user_id == user.id
    assert profile.display_name is None
    assert profile.onboarding_status == "profile_required"
    assert audit_event.user_id == user.id
    assert audit_event.event_type == "user_registered"
    assert sum(isinstance(item, CandidateProfile) for item in added) == 1
    assert sum(isinstance(item, AuditEvent) for item in added) == 1
    session.commit.assert_called_once()


def test_register_user_duplicate_does_not_add_user(monkeypatch: pytest.MonkeyPatch) -> None:
    session = Mock()
    monkeypatch.setattr("app.services.auth.get_user_by_email", lambda *_: make_user())
    with pytest.raises(DuplicateEmailError):
        register_user(session, "user@example.com", "StrongPass123", "candidate")
    session.add.assert_not_called()


def test_profile_creation_error_rolls_back_user(monkeypatch: pytest.MonkeyPatch) -> None:
    session = Mock()
    monkeypatch.setattr("app.services.auth.get_user_by_email", lambda *_: None)
    monkeypatch.setattr(
        "app.services.auth.create_empty_candidate_profile",
        Mock(side_effect=RuntimeError("profile creation failed")),
    )

    with pytest.raises(RegistrationPersistenceError):
        register_user(session, "user@example.com", "StrongPass123", "candidate")

    assert isinstance(session.add.call_args.args[0], User)
    session.rollback.assert_called_once()
    session.commit.assert_not_called()


def test_audit_creation_error_rolls_back_user_and_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    session = Mock()
    monkeypatch.setattr("app.services.auth.get_user_by_email", lambda *_: None)
    monkeypatch.setattr(
        "app.services.auth.create_user_registered_audit_event",
        Mock(side_effect=RuntimeError("audit creation failed")),
    )

    with pytest.raises(RegistrationPersistenceError):
        register_user(session, "user@example.com", "StrongPass123", "candidate")

    added = [call.args[0] for call in session.add.call_args_list]
    assert any(isinstance(item, User) for item in added)
    assert any(isinstance(item, CandidateProfile) for item in added)
    assert not any(isinstance(item, AuditEvent) for item in added)
    session.rollback.assert_called_once()
    session.commit.assert_not_called()


def test_employer_registration_does_not_create_candidate_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = Mock()
    monkeypatch.setattr("app.services.auth.get_user_by_email", lambda *_: None)

    register_user(session, "employer@example.com", "StrongPass123", "employer")

    added = [call.args[0] for call in session.add.call_args_list]
    assert not any(isinstance(item, CandidateProfile) for item in added)
    assert sum(isinstance(item, AuditEvent) for item in added) == 1


def test_inactive_user_cannot_authenticate(monkeypatch: pytest.MonkeyPatch) -> None:
    session = Mock()
    monkeypatch.setattr(
        "app.services.auth.get_user_by_email", lambda *_: make_user(status="suspended")
    )
    assert authenticate_user(session, "user@example.com", "StrongPass123") is None


def test_registration_normalizes_email_and_validates_password_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = Mock()
    monkeypatch.setattr("app.services.auth.get_user_by_email", lambda *_: None)

    user = register_user(session, "  User@Example.COM ", "StrongPass123", "candidate")

    assert user.email == "user@example.com"
    validate_registration_password("StrongPass123", "StrongPass123")
    with pytest.raises(PasswordPolicyError):
        validate_registration_password("short", "short")
    with pytest.raises(PasswordPolicyError):
        validate_registration_password("StrongPass123", "DifferentPass123")
