import io

from Bio.PDB import PDBParser

from app.bioinformatics.docking.schemas import BoundingBox


def detect_pocket_from_ligand(
    pdb_text: str,
    ligand_resname: str | None = None,
    padding: float = 4.0,
) -> BoundingBox | None:
    """Detect 3D binding pocket bounding box from a co-crystallized hetero ligand."""
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("pdb", io.StringIO(pdb_text))
    first_model = next(structure.get_models(), None)
    if not first_model:
        return None

    target_name = ligand_resname.strip().upper() if ligand_resname else None
    ligand_coords: list[tuple[float, float, float]] = []

    for chain in first_model.get_chains():
        for residue in chain.get_residues():
            if residue.id[0].startswith("H_"):
                resname = residue.resname.strip()
                if resname in ("HOH", "WAT", "DOD"):
                    continue
                if target_name is None or resname == target_name:
                    target_name = resname
                    for atom in residue.get_atoms():
                        c = atom.get_coord()
                        ligand_coords.append((float(c[0]), float(c[1]), float(c[2])))

    if not ligand_coords:
        return None

    min_x = min(c[0] for c in ligand_coords) - padding
    max_x = max(c[0] for c in ligand_coords) + padding
    min_y = min(c[1] for c in ligand_coords) - padding
    max_y = max(c[1] for c in ligand_coords) + padding
    min_z = min(c[2] for c in ligand_coords) - padding
    max_z = max(c[2] for c in ligand_coords) + padding

    cx = round((min_x + max_x) / 2.0, 2)
    cy = round((min_y + max_y) / 2.0, 2)
    cz = round((min_z + max_z) / 2.0, 2)

    # Vina boxes typically need at least 15-20 Å to allow ligand movement
    sx = max(15.0, round(max_x - min_x, 2))
    sy = max(15.0, round(max_y - min_y, 2))
    sz = max(15.0, round(max_z - min_z, 2))

    return BoundingBox(
        center_x=cx,
        center_y=cy,
        center_z=cz,
        size_x=min(40.0, sx),
        size_y=min(40.0, sy),
        size_z=min(40.0, sz),
    )


def detect_pocket_from_residues(
    pdb_text: str,
    selected_residues: list[str],
    padding: float = 6.0,
) -> BoundingBox | None:
    """Calculate bounding box surrounding a set of user-selected binding site residues."""
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("pdb", io.StringIO(pdb_text))
    first_model = next(structure.get_models(), None)
    if not first_model:
        return None

    # Parse residue targets like "ASP102" or "102" or "HIS57:A"
    clean_targets: set[str] = {r.strip().upper() for r in selected_residues}
    coords: list[tuple[float, float, float]] = []

    for chain in first_model.get_chains():
        for residue in chain.get_residues():
            resname = residue.resname.strip()
            resnum = str(residue.id[1])
            candidates = {
                f"{resname}{resnum}",
                f"{resname}{resnum}:{chain.id}",
                resnum,
            }
            if candidates.intersection(clean_targets):
                for atom in residue.get_atoms():
                    c = atom.get_coord()
                    coords.append((float(c[0]), float(c[1]), float(c[2])))

    if not coords:
        return None

    min_x = min(c[0] for c in coords) - padding
    max_x = max(c[0] for c in coords) + padding
    min_y = min(c[1] for c in coords) - padding
    max_y = max(c[1] for c in coords) + padding
    min_z = min(c[2] for c in coords) - padding
    max_z = max(c[2] for c in coords) + padding

    cx = round((min_x + max_x) / 2.0, 2)
    cy = round((min_y + max_y) / 2.0, 2)
    cz = round((min_z + max_z) / 2.0, 2)

    return BoundingBox(
        center_x=cx,
        center_y=cy,
        center_z=cz,
        size_x=min(40.0, max(16.0, round(max_x - min_x, 2))),
        size_y=min(40.0, max(16.0, round(max_y - min_y, 2))),
        size_z=min(40.0, max(16.0, round(max_z - min_z, 2))),
    )
