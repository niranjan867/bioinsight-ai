import io
import logging
from typing import Any

from Bio.PDB import PDBParser
from meeko import MoleculePreparation, PDBQTWriterLegacy
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors, rdMolDescriptors

logger = logging.getLogger(__name__)

AROMATIC_RESIDUES = {"PHE", "TYR", "TRP", "HIS"}
AROMATIC_ATOMS = {
    "PHE": {"CG", "CD1", "CD2", "CE1", "CE2", "CZ"},
    "TYR": {"CG", "CD1", "CD2", "CE1", "CE2", "CZ"},
    "TRP": {"CG", "CD1", "CD2", "NE1", "CE2", "CE3", "CZ2", "CZ3", "CH2"},
    "HIS": {"CG", "ND1", "CD2", "CE1", "NE2"},
}


class PreparationError(ValueError):
    """Raised when receptor or ligand structure fails molecular preparation."""


def prepare_receptor(
    pdb_text: str,
    remove_water: bool = True,
    altloc_mode: str = "first",
) -> tuple[str, str, dict[str, Any]]:
    """Clean, standardize, and convert a protein receptor PDB into AutoDock Vina PDBQT format.

    Returns:
        (clean_pdb_text, pdbqt_text, metadata_dict)
    """
    if not pdb_text or not pdb_text.strip():
        msg = "Empty PDB coordinates provided for receptor preparation"
        raise PreparationError(msg)

    parser = PDBParser(QUIET=True)
    try:
        structure = parser.get_structure("receptor", io.StringIO(pdb_text))
    except Exception as exc:
        msg = f"Failed to parse PDB structure: {exc}"
        raise PreparationError(msg) from exc

    first_model = next(structure.get_models(), None)
    if not first_model:
        msg = "PDB structure contains no models or atoms"
        raise PreparationError(msg)

    clean_lines: list[str] = []
    pdbqt_lines: list[str] = []
    chains_seen: set[str] = set()
    residues_seen: set[tuple[str, int]] = set()
    detected_ligands_dict: dict[tuple[str, str], int] = {}
    coords: list[tuple[float, float, float]] = []

    for chain in first_model.get_chains():
        chains_seen.add(chain.id)
        for residue in chain.get_residues():
            resname = residue.resname.strip()
            is_water = residue.id[0] == "W" or resname in ("HOH", "WAT", "DOD")
            if is_water and remove_water:
                continue

            is_hetatm = residue.id[0].startswith("H_")
            # Detect hetero ligands
            if is_hetatm:
                key = (resname, chain.id)
                detected_ligands_dict[key] = detected_ligands_dict.get(key, 0) + len(list(residue.get_atoms()))
                # Omit non-water hetero ligands from rigid receptor
                continue

            residues_seen.add((chain.id, residue.id[1]))

            for atom in residue.get_atoms():
                # Handle alternate conformations
                if altloc_mode == "first" and atom.get_altloc() not in (" ", "A", ""):
                    continue

                coord = atom.get_coord()
                coords.append((float(coord[0]), float(coord[1]), float(coord[2])))
                atom_name = atom.get_name().strip()
                element = atom.element.strip().upper() if atom.element else ""
                if not element:
                    element = atom_name[0] if not atom_name[0].isdigit() else atom_name[1]

                # Determine AutoDock atom type
                if element == "C":
                    ad_type = "A " if resname in AROMATIC_RESIDUES and atom_name in AROMATIC_ATOMS.get(resname, set()) else "C "
                elif element == "O":
                    ad_type = "OA"
                elif element == "N":
                    ad_type = "NA" if resname in AROMATIC_RESIDUES and atom_name in {"ND1", "NE2"} else "N "
                elif element == "S":
                    ad_type = "SA"
                elif element == "H":
                    ad_type = "HD"
                else:
                    ad_type = f"{element:<2}"

                # Standard PDB format line
                x, y, z = coord
                occ = atom.get_occupancy() or 1.0
                bfac = atom.get_bfactor() or 0.0
                serial = atom.get_serial_number() or 1
                resnum = residue.id[1]

                pdb_line = (
                    f"ATOM  {serial:5d} {atom_name:^4s} {resname:3s} {chain.id:1s}{resnum:4d}    "
                    f"{x:8.3f}{y:8.3f}{z:8.3f}{occ:6.2f}{bfac:6.2f}          {element:>2s}"
                )
                clean_lines.append(pdb_line)

                # AutoDock Vina PDBQT format (columns 1-66 from PDB, charge +0.000, atom type)
                base_col = pdb_line[:66].ljust(66)
                pdbqt_line = f"{base_col}     +0.000 {ad_type}"
                pdbqt_lines.append(pdbqt_line)

    if not coords:
        msg = "No standard amino acid atoms retained after receptor preparation"
        raise PreparationError(msg)

    # Compute bounding box
    min_x = min(c[0] for c in coords)
    max_x = max(c[0] for c in coords)
    min_y = min(c[1] for c in coords)
    max_y = max(c[1] for c in coords)
    min_z = min(c[2] for c in coords)
    max_z = max(c[2] for c in coords)

    center = [
        round((min_x + max_x) / 2.0, 3),
        round((min_y + max_y) / 2.0, 3),
        round((min_z + max_z) / 2.0, 3),
    ]

    detected_ligands = [
        {"chemical_id": k[0], "chain_id": k[1], "atom_count": v}
        for k, v in detected_ligands_dict.items()
    ]

    metadata = {
        "atom_count": len(coords),
        "residue_count": len(residues_seen),
        "chains": sorted(chains_seen),
        "center_xyz": center,
        "box_size_xyz": [22.0, 22.0, 22.0],
        "detected_ligands": detected_ligands,
    }

    clean_pdb_text = "\n".join(clean_lines) + "\nEND\n"
    pdbqt_text = "\n".join(pdbqt_lines) + "\n"

    return clean_pdb_text, pdbqt_text, metadata


def prepare_ligand(
    mol_input: str,
    input_type: str = "smiles",
) -> tuple[str, str, dict[str, Any]]:
    """Generate 3D conformer, calculate partial charges, and format ligand into PDBQT using RDKit and Meeko.

    Returns:
        (pdbqt_text, sdf_text, metadata_dict)
    """
    clean_input = mol_input.strip()
    if not clean_input:
        msg = "Empty ligand structure provided"
        raise PreparationError(msg)

    mol = None
    if input_type.lower() == "smiles":
        mol = Chem.MolFromSmiles(clean_input)
    elif input_type.lower() in ("sdf", "mol"):
        mol = Chem.MolFromMolBlock(clean_input)
    elif input_type.lower() == "pdb":
        mol = Chem.MolFromPDBBlock(clean_input)
    else:
        # Auto-detect format
        if "\n" in clean_input or "$$$$" in clean_input:
            mol = Chem.MolFromMolBlock(clean_input)
        else:
            mol = Chem.MolFromSmiles(clean_input)

    if mol is None:
        msg = f"RDKit could not parse the provided {input_type} ligand structure"
        raise PreparationError(msg)

    # Add explicit hydrogens
    mol = Chem.AddHs(mol)

    # 3D Conformer Generation with UFF energy minimization
    embed_res = AllChem.EmbedMolecule(mol, randomSeed=42)
    if embed_res != 0:
        # Fallback to random coordinates embedding
        AllChem.EmbedMolecule(mol, useRandomCoords=True, randomSeed=42)

    try:
        AllChem.UFFOptimizeMolecule(mol, maxIters=500)
    except Exception as exc:  # noqa: BLE001
        logger.warning("UFF optimization completed with warning: %s", exc)

    # Gasteiger partial charge calculation
    AllChem.ComputeGasteigerCharges(mol)

    # Convert to PDBQT using Meeko
    try:
        prep = MoleculePreparation()
        mol_setups = prep.prepare(mol)
        if not mol_setups:
            msg = "Meeko failed to prepare ligand torsion tree"
            raise PreparationError(msg)
        pdbqt_str, is_ok, err_msg = PDBQTWriterLegacy.write_string(mol_setups[0])
        if not is_ok:
            msg = f"Meeko PDBQT conversion error: {err_msg}"
            raise PreparationError(msg)
    except Exception as exc:
        msg = f"Ligand PDBQT generation failed: {exc}"
        raise PreparationError(msg) from exc

    # Export SDF block
    sdf_io = io.StringIO()
    writer = Chem.SDWriter(sdf_io)
    writer.write(mol)
    writer.close()
    sdf_text = sdf_io.getvalue()

    canonical_smiles = Chem.MolToSmiles(Chem.RemoveHs(mol))
    mw = round(Descriptors.MolWt(mol), 2)
    formula = rdMolDescriptors.CalcMolFormula(mol)
    rot_bonds = rdMolDescriptors.CalcNumRotatableBonds(mol)
    heavy_atoms = mol.GetNumHeavyAtoms()

    metadata = {
        "formula": formula,
        "molecular_weight": mw,
        "num_heavy_atoms": heavy_atoms,
        "num_rotatable_bonds": rot_bonds,
        "canonical_smiles": canonical_smiles,
    }

    return pdbqt_str, sdf_text, metadata
