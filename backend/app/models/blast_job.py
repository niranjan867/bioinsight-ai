from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User


class BlastJob(Base):
    """Persistent storage for NCBI BLAST queries and returned alignments."""

    __tablename__ = "blast_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    project_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    query_sequence: Mapped[str] = mapped_column(Text, nullable=False)
    program: Mapped[str] = mapped_column(String(16), nullable=False)
    database: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="SUBMITTED", nullable=False, index=True)
    ncbi_rid: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    rtoe: Mapped[int | None] = mapped_column(Integer, nullable=True)
    results: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped["User | None"] = relationship("User", foreign_keys=[user_id])
    project: Mapped["Project | None"] = relationship("Project", foreign_keys=[project_id])
