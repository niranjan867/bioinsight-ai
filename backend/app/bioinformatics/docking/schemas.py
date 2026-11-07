from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    center_x: float = Field(..., description="Box center X coordinate in Ångströms")
    center_y: float = Field(..., description="Box center Y coordinate in Ångströms")
    center_z: float = Field(..., description="Box center Z coordinate in Ångströms")
    size_x: float = Field(default=20.0, ge=5.0, le=50.0, description="Box size X in Ångströms")
    size_y: float = Field(default=20.0, ge=5.0, le=50.0, description="Box size Y in Ångströms")
    size_z: float = Field(default=20.0, ge=5.0, le=50.0, description="Box size Z in Ångströms")


class DockingConfig(BaseModel):
    exhaustiveness: int = Field(default=8, ge=1, le=32, description="Search exhaustiveness (proportional to time)")
    num_modes: int = Field(default=9, ge=1, le=20, description="Maximum number of binding poses to generate")
    energy_range: float = Field(default=3.0, ge=1.0, le=10.0, description="Maximum energy difference from best mode (kcal/mol)")
    scoring: str = Field(default="vina", description="Scoring function: vina, ad4, or vinardo")
    seed: int | None = Field(default=None, description="Explicit random seed for reproducible runs")


class ReceptorPrepRequest(BaseModel):
    pdb_id: str | None = None
    pdb_text: str | None = None
    remove_water: bool = True
    altloc_mode: str = "first"


class ReceptorPrepResponse(BaseModel):
    pdb_id: str | None = None
    atom_count: int
    residue_count: int
    chains: list[str]
    detected_ligands: list[dict[str, Any]]
    suggested_box: BoundingBox
    warnings: list[str] = Field(default_factory=list)


class LigandPrepRequest(BaseModel):
    smiles: str | None = None
    name: str | None = None
    sdf_text: str | None = None
    pubchem_cid: str | None = None


class LigandPrepResponse(BaseModel):
    name: str
    formula: str
    molecular_weight: float
    num_heavy_atoms: int
    num_rotatable_bonds: int
    canonical_smiles: str
    warnings: list[str] = Field(default_factory=list)


class PocketDetectRequest(BaseModel):
    pdb_id: str | None = None
    pdb_text: str | None = None
    ligand_resname: str | None = None
    selected_residues: list[str] | None = None
    padding: float = 4.0


class InteractionContact(BaseModel):
    chain_id: str
    residue_name: str
    residue_number: int
    atom_name: str
    ligand_atom_name: str
    distance_angstroms: float
    interaction_type: str
    protein_coord: list[float]
    ligand_coord: list[float]


class InteractionAnalysisResponse(BaseModel):
    mode_number: int
    affinity_kcal_mol: float
    hydrogen_bonds_count: int
    hydrophobic_contacts_count: int
    salt_bridges_count: int
    van_der_waals_count: int
    total_contacts: int
    interacting_residues: list[str]
    contacts: list[InteractionContact]


class DockingSubmitRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    project_id: int | None = None
    protein_source: str = Field(..., description="pdb, uniprot, alphafold, or custom")
    protein_id: str = Field(..., description="Identifier or name of target protein")
    protein_pdb_text: str | None = None
    ligand_source: str = Field(..., description="pubchem, chembl, smiles, or custom")
    ligand_id: str = Field(..., description="Identifier or SMILES of ligand")
    ligand_input: str | None = None
    binding_pocket: BoundingBox
    docking_config: DockingConfig = Field(default_factory=DockingConfig)


class DockingPoseResponse(BaseModel):
    id: int
    mode_number: int
    affinity_kcal_mol: float
    rmsd_lower_bound: float
    rmsd_upper_bound: float
    pdb_block: str
    hbond_count: int
    hydrophobic_count: int
    salt_bridge_count: int
    contacts: list[InteractionContact] = Field(default_factory=list)


class DockingJobResponse(BaseModel):
    id: str
    name: str
    status: str
    protein_name: str
    protein_source: str
    ligand_name: str
    ligand_source: str
    binding_pocket: BoundingBox
    docking_config: DockingConfig
    best_affinity: float | None = None
    execution_time_seconds: float | None = None
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class DockingJobDetailResponse(DockingJobResponse):
    poses: list[DockingPoseResponse] = Field(default_factory=list)
    receptor_pdb: str | None = None
    log_output: str | None = None
    scientific_disclaimer: str = (
        "AutoDock Vina scores are empirical computational estimates of binding free energy (kcal/mol), "
        "not experimentally determined affinities (Ki/Kd/IC50). Experimental validation (SPR, ITC, or bioassay) "
        "is required to confirm biological activity."
    )


# Legacy backward-compatible schemas for existing components
class DockingAnalysisRequest(BaseModel):
    pdb_id: str
    ligand_id: str | None = None
    max_distance: float = 4.0


class PdbLigandItem(BaseModel):
    chemical_id: str
    name: str
    chain_id: str
    atom_count: int


class PdbLigandsResponse(BaseModel):
    pdb_id: str
    ligands: list[PdbLigandItem]


class BindingPocketInfo(BaseModel):
    center_xyz: list[float]
    radius_angstroms: float
    estimated_volume_a3: float
    pocket_residues: list[str]


class DockingAnalysisResponse(BaseModel):
    pdb_id: str
    ligand_id: str
    ligand_name: str
    total_contacts: int
    hydrogen_bonds_count: int
    hydrophobic_contacts_count: int
    salt_bridges_count: int
    estimated_affinity_kcal_mol: float
    binding_score: float
    pocket: BindingPocketInfo
    contacts: list[InteractionContact]
    method: str = "3D Atomic Distance Profiling"
