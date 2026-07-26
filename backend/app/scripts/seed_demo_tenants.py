"""Seed isolated Demo Mode tenants (candidate + employer)."""

from app.db.session import SessionLocal
from app.services.demo_seed import ensure_demo_tenants


def main() -> None:
    session = SessionLocal()
    try:
        tenants = ensure_demo_tenants(session)
        print(
            "Demo tenants ready:",
            ", ".join(f"{role}={user.email}" for role, user in tenants.items()),
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
