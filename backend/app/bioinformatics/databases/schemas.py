from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DatabaseCategory(str, Enum):
    GENES = "genes"
    PROTEINS = "proteins"
    STRUCTURES = "structures"
    COMPOUNDS = "compounds"
    DISEASES = "diseases"
    PUBLICATIONS = "publications"
    PATHWAYS = "pathways"
    TARGETS = "targets"


class NormalizedRecord(BaseModel):
    """Normalized search or record result across all scientific databases."""
    id: str = Field(..., description="Primary identifier within source database")
    source_database: str = Field(..., description="Connector identifier (e.g., rcsb_pdb, uniprot)")
    database_name: str = Field(..., description="Human-readable database title")
    category: DatabaseCategory = Field(..., description="Scientific categorization")
    title: str = Field(..., description="Primary display title or symbol")
    scientific_name: str | None = Field(default=None, description="Organism or chemical scientific name")
    description: str | None = Field(default=None, description="Brief summary or abstract")
    external_url: str = Field(..., description="Canonical link to external resource")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Database-specific attributes")


class ConnectorMetadata(BaseModel):
    """Metadata describing a registered scientific database connector."""
    id: str
    name: str
    description: str
    category: DatabaseCategory
    home_url: str
    api_docs_url: str
    icon: str = "database"
    is_active: bool = True
    rate_limit_per_minute: int = 60


class ConnectorHealthStatus(BaseModel):
    """Real-time health check response for a connector."""
    database_id: str
    name: str
    is_healthy: bool
    latency_ms: float
    status_code: int | None = None
    message: str | None = None


class ConnectorSearchResult(BaseModel):
    """Results returned by a single connector."""
    database_id: str
    database_name: str
    category: DatabaseCategory
    total_hits: int = 0
    page: int = 1
    page_size: int = 10
    execution_time_ms: float = 0.0
    records: list[NormalizedRecord] = Field(default_factory=list)
    error: str | None = None


class GlobalSearchRequest(BaseModel):
    """Parameters for federated multi-database search."""
    query: str = Field(..., min_length=1, max_length=200, description="Search keyword, symbol, or ID")
    categories: list[DatabaseCategory] | None = Field(default=None, description="Filter to specific categories")
    databases: list[str] | None = Field(default=None, description="Filter to specific database IDs")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=1, le=50)


class GlobalSearchResponse(BaseModel):
    """Unified search response aggregating results across connectors."""
    query: str
    total_results: int
    execution_time_ms: float
    categories_found: list[str]
    results_by_category: dict[str, list[NormalizedRecord]]
    database_statuses: list[dict[str, Any]]
