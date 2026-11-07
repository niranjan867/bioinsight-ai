from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DiseaseSearchHit(BaseModel):
    id: str = Field(..., description="Disease identifier, e.g. EFO_0000384, MONDO:0004975")
    name: str = Field(..., description="Disease primary name")
    description: str | None = Field(None, description="Clinical description of the disease")
    entity: str = "disease"


class DiseaseSearchResponse(BaseModel):
    query: str
    total: int
    results: list[DiseaseSearchHit]


class AssociatedTarget(BaseModel):
    target_id: str = Field(..., description="Ensembl target ID")
    symbol: str = Field(..., description="Approved gene symbol")
    name: str = Field(..., description="Full target name")
    score: float = Field(..., description="Overall association score (0.0 to 1.0)")
    datatype_scores: list[dict[str, Any]] = []


class DiseaseDetailResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    therapeutic_areas: list[dict[str, str]] = []
    synonyms: list[str] = []
    source: str = "Open Targets Platform"
    associated_targets: list[AssociatedTarget] = []
    is_cached: bool = False
    retrieved_at: datetime


class PublicationHit(BaseModel):
    id: str
    title: str
    authors: str | None = None
    journal: str | None = None
    pub_year: int | None = None
    pmid: str | None = None
    pmcid: str | None = None
    doi: str | None = None
    cited_by_count: int | None = None
    source: str = "Europe PMC"


class DiseasePublicationsResponse(BaseModel):
    disease_id: str
    disease_name: str
    query: str
    total: int
    publications: list[PublicationHit]
