import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.candidate_profile import CandidateProfile
    from app.models.github_repository_snapshot import GitHubRepositorySnapshot


class GitHubRepository(TimestampMixin, Base):
    __tablename__ = "github_repositories"
    __table_args__ = (
        UniqueConstraint("candidate_id", "repository_url", name="uq_github_repositories_candidate_url"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_profiles.id"), nullable=False
    )
    repository_url: Mapped[str] = mapped_column(String(2048), nullable=False)

    candidate_profile: Mapped["CandidateProfile"] = relationship(back_populates="github_repositories")
    snapshot: Mapped["GitHubRepositorySnapshot | None"] = relationship(
        back_populates="repository", uselist=False
    )
