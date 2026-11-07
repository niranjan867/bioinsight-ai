from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class CompoundCache(Base):
    """PostgreSQL persistent cache for chemical compounds and bioactivities from PubChem and ChEMBL."""

    __tablename__ = "compound_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    compound_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    formula: Mapped[str | None] = mapped_column(String(64), nullable=True)
    smiles: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    inchi_key: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    molecular_weight: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source: Mapped[str] = mapped_column(String(64), default="pubchem", nullable=False)
    source_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_compound_cache_name_source", "name", "source"),
    )
