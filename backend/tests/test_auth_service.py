from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.core.security import hash_password
from app.models.user import User
from app.services.auth import DuplicateEmailError, authenticate_user, register_user


def make_user(role: str = "candidate", status: str = "active") -> User:
    return User(
        id=uuid4(),
        email="user@example.com",
        password_hash=hash_password("StrongPass123"),
        role=role,
        status=status,
    )


def test_register_user_hashes_password_and_sets_active(monkeypatch: pytest.MonkeyPatch) -> None:
    session = Mock()
    monkeypatch.setattr("app.services.auth.get_user_by_email", lambda *_: None)
    registered = register_user(session, "user@example.com", "StrongPass123", "candidate")
    assert registered.status == "active"
    assert registered.password_hash != "StrongPass123"
    session.commit.assert_called_once()


def test_register_user_duplicate_does_not_add_user(monkeypatch: pytest.MonkeyPatch) -> None:
    session = Mock()
    monkeypatch.setattr("app.services.auth.get_user_by_email", lambda *_: make_user())
    with pytest.raises(DuplicateEmailError):
        register_user(session, "user@example.com", "StrongPass123", "candidate")
    session.add.assert_not_called()


def test_inactive_user_cannot_authenticate(monkeypatch: pytest.MonkeyPatch) -> None:
    session = Mock()
    monkeypatch.setattr(
        "app.services.auth.get_user_by_email", lambda *_: make_user(status="blocked")
    )
    assert authenticate_user(session, "user@example.com", "StrongPass123") is None
