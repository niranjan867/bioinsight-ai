import io
import logging
import math

import numpy as np
from Bio.PDB import PDBParser

from app.bioinformatics.docking.schemas import (
    BindingPocketInfo,
    DockingAnalysisResponse,
    InteractionContact,
    PdbLigandItem,
    PdbLigandsResponse,
)
from app.bioinformatics.structures.client import StructureClient

logger = logging.getLogger(__name__)

CHARGED_BASIC = {"ARG", "LYS", "HIS"}
CHARGED_ACIDIC = {"ASP", "GLU"}
HYDROPHOBIC_RESIDUES = {"ALA", "VAL", "LEU", "ILE", "MET", "PHE", "TRP", "PRO", "TYR"}
POLAR_H_BOND_ATOMS = {"N", "O", "F", "S"}


class DockingService:
    """Calculates 3D protein-ligand atomic interactions, binding pocket geometry, and empirical affinity scores."""

    def __init__(self, structure_client: StructureClient | None = None) -> None:
        self.client = structure_client or StructureClient()

    async def get_pdb_ligands(self, pdb_id: str) -> PdbLigandsResponse:
        """Extract all bound non-water hetero-molecule ligands from a PDB structure."""
        clean_id = pdb_id.strip().upper()
        pdb_text = await self.client.get_rcsb_pdb_text(clean_id)
        if not pdb_text:
            return PdbLigandsResponse(pdb_id=clean_id, ligands=[])

        parser = PDBParser(QUIET=True)
        structure = parser.get_structure(clean_id, io.StringIO(pdb_text))
        first_model = next(structure.get_models(), None)
        if not first_model:
            return PdbLigandsResponse(pdb_id=clean_id, ligands=[])

        ligands_dict: dict[tuple[str, str], int] = {}
        for chain in first_model.get_chains():
            for residue in chain.get_residues():
                # Check for hetero-residue (HETATM)
                if residue.id[0].startswith("H_"):
                    resname = residue.resname.strip()
                    if resname not in ("HOH", "WAT", "DOD"):
                        key = (resname, chain.id)
                        atom_count = len(list(residue.get_atoms()))
                        ligands_dict[key] = ligands_dict.get(key, 0) + atom_count

        items = [
            PdbLigandItem(
                chemical_id=k[0],
                name=f"{k[0]} (Chain {k[1]})",
                chain_id=k[1],
                atom_count=v,
            )
            for k, v in ligands_dict.items()
        ]
        return PdbLigandsResponse(pdb_id=clean_id, ligands=items)

    async def analyze_interaction(
        self,
        pdb_id: str,
        ligand_id: str | None = None,
        max_distance: float = 4.0,
    ) -> DockingAnalysisResponse | None:
        """Analyze 3D atomic coordinates to detect binding pocket, contacts, and binding energy."""
        clean_id = pdb_id.strip().upper()
        pdb_text = await self.client.get_rcsb_pdb_text(clean_id)
        if not pdb_text:
            return None

        parser = PDBParser(QUIET=True)
        structure = parser.get_structure(clean_id, io.StringIO(pdb_text))
        first_model = next(structure.get_models(), None)
        if not first_model:
            return None

        # 1. Locate ligand atoms
        ligand_atoms = []
        target_ligand_name = ligand_id.strip().upper() if ligand_id else None

        for chain in first_model.get_chains():
            for residue in chain.get_residues():
                if residue.id[0].startswith("H_"):
                    resname = residue.resname.strip()
                    if resname in ("HOH", "WAT", "DOD"):
                        continue
                    if target_ligand_name is None or resname == target_ligand_name:
                        target_ligand_name = resname
                        for atom in residue.get_atoms():
                            ligand_atoms.append((chain.id, resname, atom))

        if not ligand_atoms:
            return None

        # 2. Extract protein standard residues
        protein_atoms = []
        for chain in first_model.get_chains():
            for residue in chain.get_residues():
                if residue.id[0] == " ":  # Standard amino acid
                    for atom in residue.get_atoms():
                        protein_atoms.append((chain.id, residue, atom))

        # 3. Compute 3D distance matrix and classify contacts
        contacts: list[InteractionContact] = []
        pocket_residues_set: set[str] = set()
        ligand_coords = []

        h_bonds_count = 0
        hydrophobic_count = 0
        salt_bridges_count = 0

        for l_chain, l_resname, l_atom in ligand_atoms:
            l_coord = l_atom.get_coord()
            ligand_coords.append(l_coord)
            l_element = l_atom.element.strip().upper()

            for p_chain, p_residue, p_atom in protein_atoms:
                p_coord = p_atom.get_coord()
                dist = float(np.linalg.norm(l_coord - p_coord))

                if dist <= max_distance:
                    p_resname = p_residue.resname.strip()
                    p_resnum = p_residue.id[1]
                    p_element = p_atom.element.strip().upper()
                    pocket_residues_set.add(f"{p_resname}{p_resnum}:{p_chain}")

                    # Classify interaction type
                    itype = "van_der_waals"
                    if dist <= 3.5 and l_element in POLAR_H_BOND_ATOMS and p_element in POLAR_H_BOND_ATOMS:
                        itype = "hydrogen_bond"
                        h_bonds_count += 1
                    elif (
                        dist <= 4.0
                        and l_element == "C"
                        and p_element == "C"
                        and p_resname in HYDROPHOBIC_RESIDUES
                    ):
                        itype = "hydrophobic"
                        hydrophobic_count += 1
                    elif (
                        dist <= 4.0
                        and (
                            (p_resname in CHARGED_BASIC and l_element in ("O", "S", "P"))
                            or (p_resname in CHARGED_ACIDIC and l_element == "N")
                        )
                    ):
                        itype = "salt_bridge"
                        salt_bridges_count += 1

                    contacts.append(
                        InteractionContact(
                            chain_id=p_chain,
                            residue_name=p_resname,
                            residue_number=p_resnum,
                            atom_name=p_atom.get_name().strip(),
                            ligand_atom_name=l_atom.get_name().strip(),
                            distance_angstroms=round(dist, 2),
                            interaction_type=itype,
                        )
                    )

        # Sort contacts by distance ascending
        contacts.sort(key=lambda c: c.distance_angstroms)

        # 4. Calculate pocket geometry
        coords_arr = np.array(ligand_coords)
        center = np.mean(coords_arr, axis=0).tolist()
        radius = float(np.max(np.linalg.norm(coords_arr - center, axis=1))) + max_distance
        volume_estimate = round((4.0 / 3.0) * math.pi * (radius**3), 2)

        # 5. Compute empirical binding energy (kcal/mol)
        vdw_count = max(0, len(contacts) - h_bonds_count - hydrophobic_count - salt_bridges_count)
        delta_g = (
            -0.6 * h_bonds_count
            - 0.8 * salt_bridges_count
            - 0.25 * hydrophobic_count
            - 0.08 * vdw_count
        )
        delta_g = round(delta_g, 2)

        # Scaled binding score (0 to 100)
        binding_score = min(100.0, max(10.0, abs(delta_g) * 6.5 + len(contacts) * 0.5))
        binding_score = round(binding_score, 1)

        return DockingAnalysisResponse(
            pdb_id=clean_id,
            ligand_id=target_ligand_name or "LIG",
            ligand_name=f"Bound Hetero-Molecule {target_ligand_name}",
            total_contacts=len(contacts),
            hydrogen_bonds_count=h_bonds_count,
            hydrophobic_contacts_count=hydrophobic_count,
            salt_bridges_count=salt_bridges_count,
            estimated_affinity_kcal_mol=delta_g,
            binding_score=binding_score,
            pocket=BindingPocketInfo(
                center_xyz=[round(x, 2) for x in center],
                radius_angstroms=round(radius, 2),
                estimated_volume_a3=volume_estimate,
                pocket_residues=sorted(pocket_residues_set),
            ),
            contacts=contacts[:100],  # Return top 100 closest contacts
        )
