import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.github_repository import GitHubRepository


class GitHubRepositorySnapshot(TimestampMixin, Base):
    __tablename__ = "github_repository_snapshots"
    __table_args__ = (
        CheckConstraint(
            "char_length(checksum) = 64", name="ck_github_repository_snapshots_checksum"
        ),
        UniqueConstraint("repository_id", name="uq_github_repository_snapshots_repository_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("github_repositories.id"), nullable=False
    )
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)

    repository: Mapped["GitHubRepository"] = relationship(back_populates="snapshot")
