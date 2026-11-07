from pydantic import BaseModel, Field


class InteractionContact(BaseModel):
    chain_id: str
    residue_name: str
    residue_number: int
    atom_name: str
    ligand_atom_name: str
    distance_angstroms: float = Field(..., description="Euclidean distance in Angstroms")
    interaction_type: str = Field(..., description="hydrogen_bond, hydrophobic, salt_bridge, or van_der_waals")


class BindingPocketInfo(BaseModel):
    center_xyz: list[float]
    radius_angstroms: float
    estimated_volume_a3: float
    pocket_residues: list[str]


class DockingAnalysisRequest(BaseModel):
    pdb_id: str = Field(..., min_length=4, max_length=10, description="4-letter PDB ID (e.g. 4HHB, 1IEP, 3WZE)")
    ligand_id: str | None = Field(None, description="Ligand 3-letter chemical code (e.g. HEM, STI, ATP). If omitted, the first bound ligand is selected.")
    max_distance: float = Field(default=4.0, ge=2.5, le=7.0, description="Contact cutoff distance in Angstroms")


class DockingAnalysisResponse(BaseModel):
    pdb_id: str
    ligand_id: str
    ligand_name: str
    total_contacts: int
    hydrogen_bonds_count: int
    hydrophobic_contacts_count: int
    salt_bridges_count: int
    estimated_affinity_kcal_mol: float = Field(..., description="Empirical estimated binding free energy (kcal/mol)")
    binding_score: float = Field(..., description="Interaction quality index (0 to 100)")
    pocket: BindingPocketInfo
    contacts: list[InteractionContact]
    method: str = "Biopython PDB 3D Atomic Distance & Empirical Contact Scoring"


class PdbLigandItem(BaseModel):
    chemical_id: str
    name: str
    chain_id: str
    atom_count: int


class PdbLigandsResponse(BaseModel):
    pdb_id: str
    ligands: list[PdbLigandItem]
