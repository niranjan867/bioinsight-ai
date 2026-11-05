from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class GeneCache(Base):
    """PostgreSQL cache for external gene metadata retrieved from trusted biological sources.

    Preserves source identifiers, retrieval timestamps, and parsed annotations.
    """

    __tablename__ = "gene_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    gene_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    symbol: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    species: Mapped[str] = mapped_column(String(64), index=True, default="human", nullable=False)
    taxid: Mapped[int | None] = mapped_column(Integer, nullable=True)
    entrez_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    ensembl_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    chromosome: Mapped[str | None] = mapped_column(String(32), nullable=True)
    genomic_start: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    genomic_end: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    strand: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    type_of_gene: Mapped[str | None] = mapped_column(String(64), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    aliases: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(64), default="mygene.info", nullable=False)
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
        Index("ix_gene_cache_symbol_species", "symbol", "species"),
    )
