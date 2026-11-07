from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class CitationItem(BaseModel):
    source: str = Field(..., description="MyGene.info, UniProtKB, Open Targets, PubChem, PDB, or Europe PMC")
    identifier: str = Field(..., description="Accession, symbol, CID, or EFO ID")
    title: str = Field(..., description="Target name or publication title")
    url: str | None = None


class AssistantQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000, description="Scientific research question or prompt")
    context_type: str | None = Field(default=None, description="Optional entity context: gene, protein, disease, compound, or docking")
    context_id: str | None = Field(default=None, description="Optional entity ID (e.g. BRCA1, P68871, 2244)")
    history: list[ChatMessage] = Field(default=[], description="Previous conversation turn history")


class AssistantQueryResponse(BaseModel):
    answer: str = Field(..., description="Evidence-grounded scientific synthesis")
    citations: list[CitationItem] = []
    confidence: float = Field(default=1.0, description="Evidence confidence score")
    source_modules: list[str] = []
    engine: str = "BioInsight Grounded Scientific Engine"
