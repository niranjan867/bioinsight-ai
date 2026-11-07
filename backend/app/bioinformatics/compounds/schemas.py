from datetime import datetime

from pydantic import BaseModel, Field


class LipinskiRuleOfFive(BaseModel):
    molecular_weight_pass: bool = Field(..., description="Molecular weight <= 500 Da")
    logp_pass: bool = Field(..., description="Calculated LogP <= 5.0")
    h_bond_donors_pass: bool = Field(..., description="H-bond donors <= 5")
    h_bond_acceptors_pass: bool = Field(..., description="H-bond acceptors <= 10")
    violations_count: int = Field(..., description="Number of Lipinski violations (0-4)")
    is_druglike: bool = Field(..., description="True if violations <= 1")


class CompoundSearchHit(BaseModel):
    cid: int
    name: str
    molecular_formula: str | None = None
    molecular_weight: float | None = None
    canonical_smiles: str | None = None
    inchi_key: str | None = None
    image_url: str


class CompoundSearchResponse(BaseModel):
    query: str
    total: int
    results: list[CompoundSearchHit]


class DrugTargetRelationship(BaseModel):
    mechanism_of_action: str
    target_name: str
    target_chembl_id: str | None = None
    action_type: str | None = None
    references: list[str] = []


class CompoundDetailResponse(BaseModel):
    cid: int
    name: str
    iupac_name: str | None = None
    molecular_formula: str | None = None
    molecular_weight: float | None = None
    canonical_smiles: str | None = None
    isomeric_smiles: str | None = None
    inchi_key: str | None = None
    xlogp: float | None = None
    tpsa: float | None = None
    h_bond_donor_count: int | None = None
    h_bond_acceptor_count: int | None = None
    rotatable_bond_count: int | None = None
    exact_mass: float | None = None
    image_url: str
    lipinski: LipinskiRuleOfFive
    chembl_id: str | None = None
    drug_targets: list[DrugTargetRelationship] = []
    source: str = "PubChem / ChEMBL"
    is_cached: bool = False
    retrieved_at: datetime


class CompoundTargetsResponse(BaseModel):
    cid: int
    name: str
    chembl_id: str | None = None
    targets: list[DrugTargetRelationship]
    source: str = "ChEMBL"


class Compound3DConformerResponse(BaseModel):
    cid: int
    name: str
    format: str = "sdf"
    sdf_data: str
