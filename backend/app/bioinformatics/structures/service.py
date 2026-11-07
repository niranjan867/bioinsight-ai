import io
import logging
from datetime import UTC, datetime

from Bio.PDB import PDBParser

from app.bioinformatics.structures.client import StructureClient
from app.bioinformatics.structures.schemas import (
    AlphaFoldMetadataResponse,
    BoundLigand,
    PolymerEntity,
    StructureMetadataResponse,
)

logger = logging.getLogger(__name__)


class StructureService:
    """Orchestrates 3D structure retrieval, coordinate validation, and Biopython parsing."""

    def __init__(self, client: StructureClient | None = None) -> None:
        self.client = client or StructureClient()

    async def get_structure_metadata(self, structure_id: str) -> StructureMetadataResponse | None:
        """Fetch experimental structure metadata from RCSB PDB and compute coordinate statistics."""
        clean_id = structure_id.strip().upper()
        raw = await self.client.get_rcsb_entry(clean_id)
        if not raw:
            return None

        struct_info = raw.get("struct", {})
        title = struct_info.get("title", f"PDB Entry {clean_id}")

        exptl = raw.get("exptl", [{}])
        method = exptl[0].get("method", "X-RAY DIFFRACTION") if exptl else "X-RAY DIFFRACTION"

        refine = raw.get("refine", [{}])
        resolution = None
        if refine and refine[0].get("ls_d_res_high"):
            try:
                resolution = float(refine[0]["ls_d_res_high"])
            except ValueError:
                pass
        elif raw.get("rcsb_entry_info", {}).get("resolution_combined"):
            try:
                resolution = float(raw["rcsb_entry_info"]["resolution_combined"][0])
            except (ValueError, IndexError):
                pass

        release_date = raw.get("rcsb_accession_info", {}).get("initial_release_date")

        # Polymers
        polymers: list[PolymerEntity] = []
        polymer_container = raw.get("rcsb_entry_container_identifiers", {}).get("polymer_entity_ids", [])
        for pid in polymer_container:
            polymers.append(
                PolymerEntity(
                    entity_id=str(pid),
                    description=f"Polymer Entity {pid}",
                    chain_ids=[],
                )
            )

        # Non-polymer ligands
        ligands: list[BoundLigand] = []
        nonpolymer_container = raw.get("rcsb_entry_container_identifiers", {}).get("non_polymer_entity_ids", [])
        for nid in nonpolymer_container:
            ligands.append(
                BoundLigand(
                    chemical_id=str(nid),
                    name=f"Ligand Entity {nid}",
                )
            )

        # Parse real PDB coordinates with Biopython to extract exact chains, residues, and atoms
        chains: list[str] = []
        total_residues = 0
        total_atoms = 0

        pdb_text = await self.client.get_rcsb_pdb_text(clean_id)
        if pdb_text:
            try:
                parser = PDBParser(QUIET=True)
                structure = parser.get_structure(clean_id, io.StringIO(pdb_text))
                first_model = next(structure.get_models(), None)
                if first_model:
                    for chain in first_model.get_chains():
                        chains.append(chain.id)
                        for residue in chain.get_residues():
                            # Standard amino acid or nucleotide
                            if residue.id[0] == " ":
                                total_residues += 1
                            elif residue.id[0].startswith("H_"):
                                # Check if ligand
                                chem_id = residue.resname.strip()
                                if chem_id not in [lig.chemical_id for lig in ligands] and chem_id != "HOH":
                                    ligands.append(
                                        BoundLigand(
                                            chemical_id=chem_id,
                                            name=chem_id,
                                            chain_id=chain.id,
                                        )
                                    )
                            for _ in residue.get_atoms():
                                total_atoms += 1
            except (ValueError, KeyError, IndexError, AttributeError) as exc:
                logger.warning("Biopython parsing warning for PDB %s: %s", clean_id, exc)

        return StructureMetadataResponse(
            structure_id=clean_id,
            title=title,
            experimental_method=method,
            resolution=resolution,
            release_date=release_date,
            is_experimental=True,
            polymer_entities=polymers,
            bound_ligands=ligands,
            chains=chains,
            total_residues=total_residues,
            total_atoms=total_atoms,
            source="RCSB Protein Data Bank",
            retrieved_at=datetime.now(UTC),
        )

    async def get_alphafold_metadata(self, accession: str) -> AlphaFoldMetadataResponse | None:
        """Fetch AlphaFold DB predicted model metadata and confidence score."""
        clean_acc = accession.strip().upper()
        data = await self.client.get_alphafold_prediction(clean_acc)
        if not data:
            return None

        plddt = float(data.get("globalMetricValue", 85.0))
        if plddt >= 90.0:
            category = "Very High (>90)"
        elif plddt >= 70.0:
            category = "Confident (70-90)"
        elif plddt >= 50.0:
            category = "Low (50-70)"
        else:
            category = "Very Low (<50)"

        return AlphaFoldMetadataResponse(
            uniprot_accession=clean_acc,
            entry_id=data.get("entryId", f"AF-{clean_acc}-F1"),
            gene_symbol=data.get("gene"),
            organism=data.get("organismScientificName", "Homo sapiens"),
            global_plddt=round(plddt, 2),
            confidence_category=category,
            model_url=data.get("pdbUrl", ""),
            pdb_url=data.get("pdbUrl", ""),
            cif_url=data.get("cifUrl", ""),
            is_experimental=False,
            source="AlphaFold Protein Structure Database",
            retrieved_at=datetime.now(UTC),
        )

    async def get_pdb_file_content(self, structure_id: str) -> str | None:
        """Fetch raw PDB format text content from RCSB or AlphaFold DB."""
        clean_id = structure_id.strip()
        if len(clean_id) == 4 and clean_id.isalnum():
            # RCSB PDB ID (e.g. 4HHB, 1CRN)
            return await self.client.get_rcsb_pdb_text(clean_id)
        # Try AlphaFold accession
        af_meta = await self.get_alphafold_metadata(clean_id)
        if af_meta and af_meta.pdb_url:
            return await self.client.get_alphafold_pdb_text(af_meta.pdb_url)
        return None
