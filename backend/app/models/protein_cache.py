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


class ProteinCache(Base):
    """PostgreSQL persistent cache for biological protein annotations from UniProtKB, RCSB PDB, and AlphaFold.

    Stores sequence data, physicochemical summaries, structural links, and provenance timestamps.
    """

    __tablename__ = "protein_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    accession: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    entry_name: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    protein_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    gene_name: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    organism: Mapped[str] = mapped_column(String(128), index=True, default="Homo sapiens", nullable=False)
    taxid: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    sequence: Mapped[str] = mapped_column(Text, nullable=False)
    length: Mapped[int] = mapped_column(Integer, nullable=False)
    mass: Mapped[int | None] = mapped_column(Integer, nullable=True)
    function_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    subcellular_location: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(64), default="UniProtKB", nullable=False)
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
        Index("ix_protein_cache_gene_organism", "gene_name", "organism"),
        Index("ix_protein_cache_name_organism", "protein_name", "organism"),
    )
