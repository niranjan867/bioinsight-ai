import io

import numpy as np
from Bio.PDB import PDBParser

from app.bioinformatics.docking.schemas import (
    InteractionAnalysisResponse,
    InteractionContact,
)

POLAR_H_BOND_ATOMS = {"N", "O", "F", "S"}
HYDROPHOBIC_RESIDUES = {"ALA", "VAL", "LEU", "ILE", "MET", "PHE", "TRP", "PRO", "TYR"}
BASIC_RESIDUES = {"ARG", "LYS", "HIS"}
ACIDIC_RESIDUES = {"ASP", "GLU"}


def analyze_pose_interactions(
    receptor_pdb: str,
    docked_pose_pdb: str,
    mode_number: int = 1,
    affinity_kcal_mol: float = 0.0,
    max_distance: float = 4.2,
) -> InteractionAnalysisResponse:
    """Detect and classify 3D geometric atomic interactions between docked ligand and protein receptor."""
    parser = PDBParser(QUIET=True)

    # 1. Parse receptor atoms
    rec_structure = parser.get_structure("receptor", io.StringIO(receptor_pdb))
    rec_model = next(rec_structure.get_models(), None)
    protein_atoms = []
    if rec_model:
        for chain in rec_model.get_chains():
            for residue in chain.get_residues():
                if residue.id[0] == " ":  # Standard amino acid
                    for atom in residue.get_atoms():
                        protein_atoms.append((chain.id, residue, atom))

    # 2. Parse ligand pose atoms
    lig_structure = parser.get_structure("ligand", io.StringIO(docked_pose_pdb))
    lig_model = next(lig_structure.get_models(), None)
    ligand_atoms = []
    if lig_model:
        for chain in lig_model.get_chains():
            for residue in chain.get_residues():
                ligand_atoms.extend(list(residue.get_atoms()))

    contacts: list[InteractionContact] = []
    seen_pairs: set[tuple[str, int, str, str]] = set()
    hbond_count = 0
    hydrophobic_count = 0
    salt_bridge_count = 0
    vdw_count = 0
    interacting_res_set: set[str] = set()

    for l_atom in ligand_atoms:
        l_coord = l_atom.get_coord()
        l_elem = l_atom.element.strip().upper() if l_atom.element else l_atom.get_name().strip()[:1].upper()
        if l_elem == "H":
            continue

        for p_chain, p_residue, p_atom in protein_atoms:
            p_elem = p_atom.element.strip().upper() if p_atom.element else p_atom.get_name().strip()[:1].upper()
            if p_elem == "H":
                continue

            p_coord = p_atom.get_coord()
            dist = float(np.linalg.norm(l_coord - p_coord))

            if dist <= max_distance:
                p_resname = p_residue.resname.strip()
                p_resnum = p_residue.id[1]
                p_atom_name = p_atom.get_name().strip()
                l_atom_name = l_atom.get_name().strip()

                pair_key = (p_chain, p_resnum, p_atom_name, l_atom_name)
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                # Classify interaction type
                itype = "van_der_waals"
                if dist <= 3.5 and l_elem in POLAR_H_BOND_ATOMS and p_elem in POLAR_H_BOND_ATOMS:
                    itype = "hydrogen_bond"
                    hbond_count += 1
                elif dist <= 4.0 and l_elem == "C" and p_elem == "C" and p_resname in HYDROPHOBIC_RESIDUES:
                    itype = "hydrophobic"
                    hydrophobic_count += 1
                elif dist <= 4.0 and (
                    (p_resname in BASIC_RESIDUES and l_elem in ("O", "S"))
                    or (p_resname in ACIDIC_RESIDUES and l_elem == "N")
                ):
                    itype = "salt_bridge"
                    salt_bridge_count += 1
                else:
                    vdw_count += 1

                res_label = f"{p_resname}{p_resnum}:{p_chain}"
                interacting_res_set.add(res_label)

                contacts.append(
                    InteractionContact(
                        chain_id=p_chain,
                        residue_name=p_resname,
                        residue_number=p_resnum,
                        atom_name=p_atom_name,
                        ligand_atom_name=l_atom_name,
                        distance_angstroms=round(dist, 2),
                        interaction_type=itype,
                        protein_coord=[round(float(c), 3) for c in p_coord],
                        ligand_coord=[round(float(c), 3) for c in l_coord],
                    )
                )

    # Sort contacts by distance ascending
    contacts.sort(key=lambda c: c.distance_angstroms)

    return InteractionAnalysisResponse(
        mode_number=mode_number,
        affinity_kcal_mol=affinity_kcal_mol,
        hydrogen_bonds_count=hbond_count,
        hydrophobic_contacts_count=hydrophobic_count,
        salt_bridges_count=salt_bridge_count,
        van_der_waals_count=vdw_count,
        total_contacts=len(contacts),
        interacting_residues=sorted(interacting_res_set),
        contacts=contacts[:100],  # Return top 100 contacts
    )
