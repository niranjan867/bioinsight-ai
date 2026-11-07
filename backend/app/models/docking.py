from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User


class DockingJob(Base):
    """Persistent molecular docking job record executed via AutoDock Vina."""

    __tablename__ = "docking_jobs"

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
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="QUEUED", nullable=False, index=True)
    protein_name: Mapped[str] = mapped_column(String(255), nullable=False)
    protein_source: Mapped[str] = mapped_column(String(64), nullable=False)
    ligand_name: Mapped[str] = mapped_column(String(255), nullable=False)
    ligand_source: Mapped[str] = mapped_column(String(64), nullable=False)
    binding_pocket: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    docking_config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    receptor_storage_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    ligand_storage_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    output_storage_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    best_affinity: Mapped[float | None] = mapped_column(Float, nullable=True)
    execution_time_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    log_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
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
    poses: Mapped[list["DockingPose"]] = relationship(
        "DockingPose",
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="DockingPose.mode_number",
    )


class DockingPose(Base):
    """Ranked 3D binding conformation and interaction profile generated from docking."""

    __tablename__ = "docking_poses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("docking_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mode_number: Mapped[int] = mapped_column(Integer, nullable=False)
    affinity_kcal_mol: Mapped[float] = mapped_column(Float, nullable=False)
    rmsd_lower_bound: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    rmsd_upper_bound: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    pdb_block: Mapped[str] = mapped_column(Text, nullable=False)
    contacts: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    hbond_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    hydrophobic_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    salt_bridge_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    job: Mapped["DockingJob"] = relationship("DockingJob", back_populates="poses")

    __table_args__ = (
        Index("ix_docking_pose_job_mode", "job_id", "mode_number"),
    )
