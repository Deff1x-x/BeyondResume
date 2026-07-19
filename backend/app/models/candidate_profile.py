import uuid
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum as SqlEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.evidence_unit import EvidenceUnit
    from app.models.evidence_skill_link import EvidenceSkillLink
    from app.models.github_repository import GitHubRepository
    from app.models.resume import Resume
    from app.models.user import User


class OnboardingStatus(str, Enum):
    PROFILE_REQUIRED = "profile_required"


class CandidateProfile(TimestampMixin, Base):
    __tablename__ = "candidate_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True
    )
    display_name: Mapped[str | None] = mapped_column("full_name", String(150), nullable=True)
    target_role: Mapped[str | None] = mapped_column("desired_role", String(80), nullable=True)
    location: Mapped[str | None] = mapped_column("country", String(80), nullable=True)
    remote_preference: Mapped[str | None] = mapped_column("work_format", String(50), nullable=True)
    english_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    availability: Mapped[str | None] = mapped_column(String(100), nullable=True)
    summary: Mapped[str | None] = mapped_column("bio", Text, nullable=True)
    data_processing_consent: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    onboarding_status: Mapped[OnboardingStatus] = mapped_column(
        SqlEnum(
            OnboardingStatus,
            name="candidate_onboarding_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    salary_expectation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    preferred_employment_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    relocation_readiness: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    portfolio_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    user: Mapped["User"] = relationship(back_populates="candidate_profile")
    resumes: Mapped[list["Resume"]] = relationship(back_populates="candidate_profile")
    github_repository: Mapped["GitHubRepository | None"] = relationship(
        back_populates="candidate_profile", uselist=False
    )
    evidence_units: Mapped[list["EvidenceUnit"]] = relationship(back_populates="candidate_profile")
    evidence_skill_links: Mapped[list["EvidenceSkillLink"]] = relationship(
        back_populates="candidate_profile"
    )
