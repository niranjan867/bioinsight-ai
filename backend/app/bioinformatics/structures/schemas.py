from datetime import datetime

from pydantic import BaseModel, Field


class PolymerEntity(BaseModel):
    entity_id: str
    description: str
    chain_ids: list[str] = []
    length: int | None = None
    organism: str | None = None


class BoundLigand(BaseModel):
    chemical_id: str
    name: str
    formula: str | None = None
    molecular_weight: float | None = None
    chain_id: str | None = None


class StructureMetadataResponse(BaseModel):
    structure_id: str = Field(..., description="4-letter PDB ID or AlphaFold accession")
    title: str = Field(..., description="Experimental title or predicted macromolecule")
    experimental_method: str = Field(..., description="X-RAY DIFFRACTION, CRYO-EM, SOLUTION NMR, or COMPUTATIONAL")
    resolution: float | None = Field(None, description="Structure resolution in Angstroms (if experimental)")
    release_date: str | None = None
    is_experimental: bool = True
    polymer_entities: list[PolymerEntity] = []
    bound_ligands: list[BoundLigand] = []
    chains: list[str] = []
    total_residues: int = 0
    total_atoms: int = 0
    source: str = "RCSB Protein Data Bank"
    retrieved_at: datetime


class AlphaFoldMetadataResponse(BaseModel):
    uniprot_accession: str
    entry_id: str
    gene_symbol: str | None = None
    organism: str
    global_plddt: float = Field(..., description="Average predicted Local Distance Difference Test (0-100)")
    confidence_category: str = Field(..., description="Very High (>90), Confident (70-90), Low (50-70), Very Low (<50)")
    model_url: str
    pdb_url: str
    cif_url: str
    is_experimental: bool = False
    source: str = "AlphaFold Protein Structure Database"
    retrieved_at: datetime
