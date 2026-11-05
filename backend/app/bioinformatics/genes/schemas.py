from pydantic import BaseModel, Field


class GenomicLocation(BaseModel):
    """Genomic coordinates and orientation for a gene locus."""

    chromosome: str | None = Field(default=None, description="Chromosome or contig identifier")
    start: int | None = Field(default=None, description="Genomic start coordinate (1-based)")
    end: int | None = Field(default=None, description="Genomic end coordinate (1-based)")
    strand: int | None = Field(default=None, description="DNA strand orientation (+1 for forward, -1 for reverse)")
    ensembl_gene_id: str | None = Field(default=None, description="Associated Ensembl gene identifier")


class DatabaseReference(BaseModel):
    """Cross-reference link to trusted external biological database."""

    database: str = Field(description="Database name, e.g., NCBI Gene, Ensembl, HGNC, OMIM, GeneCards")
    identifier: str = Field(description="Accession number or identifier in target database")
    url: str = Field(description="Direct web link to the biological record")
    description: str | None = Field(default=None, description="Short description of the cross-reference")


class GeneSearchResult(BaseModel):
    """Single gene hit from multi-database query."""

    id: str = Field(description="Primary biological gene identifier (Entrez ID or MyGene ID)")
    symbol: str = Field(description="Official gene symbol, e.g., BRCA1, TP53")
    name: str | None = Field(default=None, description="Full descriptive gene name")
    species: str = Field(description="Organism common or scientific name")
    taxid: int | None = Field(default=None, description="NCBI Taxonomy identifier")
    entrez_id: str | None = Field(default=None, description="NCBI Entrez Gene ID")
    ensembl_id: str | None = Field(default=None, description="Ensembl Gene ID")
    chromosome: str | None = Field(default=None, description="Chromosomal location")
    type_of_gene: str | None = Field(default=None, description="Biotype, e.g., protein-coding, ncRNA, pseudo")
    aliases: list[str] = Field(default_factory=list, description="Approved gene synonyms and previous symbols")
    score: float | None = Field(default=None, description="Search relevance score")


class GeneSearchResponse(BaseModel):
    """Response payload for gene search query."""

    query: str = Field(description="Search input query")
    species: str = Field(description="Organism filter applied")
    total: int = Field(description="Total number of matching genes discovered")
    results: list[GeneSearchResult] = Field(description="Ranked gene hits")
    source: str = Field(default="MyGene.info / NCBI Entrez", description="Origin of primary biological data")


class GeneDetailResponse(BaseModel):
    """Comprehensive biological record for an inspected gene."""

    id: str = Field(description="Primary gene identifier")
    symbol: str = Field(description="Official gene symbol")
    name: str | None = Field(default=None, description="Full scientific gene name")
    species: str = Field(description="Organism")
    taxid: int | None = Field(default=None, description="NCBI Taxonomy ID")
    entrez_id: str | None = Field(default=None, description="NCBI Entrez Gene ID")
    ensembl_id: str | None = Field(default=None, description="Ensembl Gene ID")
    type_of_gene: str | None = Field(default=None, description="Gene biotype category")
    chromosome: str | None = Field(default=None, description="Chromosome")
    genomic_location: GenomicLocation | None = Field(default=None, description="Genomic coordinates and orientation")
    aliases: list[str] = Field(default_factory=list, description="Official gene aliases and synonyms")
    summary: str | None = Field(default=None, description="Curated biological function summary")
    references: list[DatabaseReference] = Field(default_factory=list, description="Verified cross-references")
    source: str = Field(description="Attribution of external data source")
    retrieved_at: str = Field(description="ISO timestamp of data retrieval")
    cached: bool = Field(description="Whether response was served from PostgreSQL cache")


class GeneReferencesResponse(BaseModel):
    """Direct cross-references and external links for a gene record."""

    gene_id: str = Field(description="Gene identifier")
    symbol: str = Field(description="Official gene symbol")
    references: list[DatabaseReference] = Field(description="List of outbound biological database links")
    source: str = Field(default="NCBI Entrez / Ensembl / HGNC", description="Cross-reference provider")

