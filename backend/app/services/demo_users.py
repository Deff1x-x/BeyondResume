"""Demo Mode identity helpers."""

from __future__ import annotations

from app.api.errors import api_error
from app.models.user import User

DEMO_EMAIL_DOMAIN = "beyondresume.dev"
DEMO_CANDIDATE_EMAIL = f"demo.candidate@{DEMO_EMAIL_DOMAIN}"
DEMO_CANDIDATE_B_EMAIL = f"demo.candidate.b@{DEMO_EMAIL_DOMAIN}"
DEMO_CANDIDATE_C_EMAIL = f"demo.candidate.c@{DEMO_EMAIL_DOMAIN}"
DEMO_CANDIDATE_D_EMAIL = f"demo.candidate.d@{DEMO_EMAIL_DOMAIN}"
DEMO_EMPLOYER_EMAIL = f"demo.employer@{DEMO_EMAIL_DOMAIN}"
DEMO_PASSWORD = "DemoMode!Pass123"

DEMO_CANDIDATE_EMAILS = (
    DEMO_CANDIDATE_EMAIL,
    DEMO_CANDIDATE_B_EMAIL,
    DEMO_CANDIDATE_C_EMAIL,
    DEMO_CANDIDATE_D_EMAIL,
)


def is_demo_email(email: str | None) -> bool:
    if not email:
        return False
    return str(email).lower().endswith(f"@{DEMO_EMAIL_DOMAIN}")


def is_demo_user(user: User | None) -> bool:
    return user is not None and is_demo_email(user.email)


def reject_demo_fixture_mutation(user: User, *, action: str) -> None:
    """Block permanent/fixture-changing mutations for isolated demo tenants."""
    if is_demo_user(user):
        raise api_error(
            403,
            "DEMO_MUTATION_FORBIDDEN",
            f"Demo Mode cannot {action}. Use Restart Demo to restore the workspace.",
        )
