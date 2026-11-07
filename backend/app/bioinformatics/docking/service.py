import io
import logging
import math
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from Bio.PDB import PDBParser
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.bioinformatics.docking.engine import run_autodock_vina
from app.bioinformatics.docking.interactions import analyze_pose_interactions
from app.bioinformatics.docking.pocket import (
    detect_pocket_from_ligand,
    detect_pocket_from_residues,
)
from app.bioinformatics.docking.preparation import prepare_ligand, prepare_receptor
from app.bioinformatics.docking.schemas import (
    BindingPocketInfo,
    BoundingBox,
    DockingAnalysisResponse,
    DockingConfig,
    DockingJobDetailResponse,
    DockingJobResponse,
    DockingPoseResponse,
    DockingSubmitRequest,
    InteractionContact,
    LigandPrepRequest,
    LigandPrepResponse,
    PdbLigandItem,
    PdbLigandsResponse,
    PocketDetectRequest,
    ReceptorPrepRequest,
    ReceptorPrepResponse,
)
from app.bioinformatics.structures.client import StructureClient
from app.database.session import SessionLocal
from app.models.docking import DockingJob, DockingPose

logger = logging.getLogger(__name__)

CHARGED_BASIC = {"ARG", "LYS", "HIS"}
CHARGED_ACIDIC = {"ASP", "GLU"}
HYDROPHOBIC_RESIDUES = {"ALA", "VAL", "LEU", "ILE", "MET", "PHE", "TRP", "PRO", "TYR"}
POLAR_H_BOND_ATOMS = {"N", "O", "F", "S"}

_executor = ThreadPoolExecutor(max_workers=4)


class DockingService:
    """Enterprise molecular docking service managing AutoDock Vina, preparation, and persistent jobs."""

    def __init__(self, structure_client: StructureClient | None = None) -> None:
        self.structure_client = structure_client or StructureClient()

    # ---------------------------------------------------------
    # 1. Molecular Preparation & Pocket Detection
    # ---------------------------------------------------------

    async def prepare_receptor_input(self, req: ReceptorPrepRequest) -> ReceptorPrepResponse:
        """Fetch, clean, and analyze receptor structure for docking."""
        pdb_text = req.pdb_text
        if not pdb_text and req.pdb_id:
            pdb_text = await self.structure_client.get_rcsb_pdb_text(req.pdb_id.strip().upper())
            if not pdb_text:
                msg = f"Structure for PDB ID '{req.pdb_id}' could not be retrieved from RCSB."
                raise ValueError(msg)

        if not pdb_text:
            msg = "Either pdb_id or pdb_text must be provided."
            raise ValueError(msg)

        _clean_pdb, _, meta = prepare_receptor(pdb_text, remove_water=req.remove_water, altloc_mode=req.altloc_mode)

        # Detect suggested box
        suggested_box = detect_pocket_from_ligand(pdb_text)
        if not suggested_box:
            c = meta["center_xyz"]
            suggested_box = BoundingBox(
                center_x=c[0],
                center_y=c[1],
                center_z=c[2],
                size_x=22.0,
                size_y=22.0,
                size_z=22.0,
            )

        return ReceptorPrepResponse(
            pdb_id=req.pdb_id,
            atom_count=meta["atom_count"],
            residue_count=meta["residue_count"],
            chains=meta["chains"],
            detected_ligands=meta["detected_ligands"],
            suggested_box=suggested_box,
            warnings=[],
        )

    async def prepare_ligand_input(self, req: LigandPrepRequest) -> LigandPrepResponse:
        """Validate, generate 3D conformer, and prepare ligand."""
        input_str = req.smiles or req.sdf_text
        input_type = "smiles" if req.smiles else "sdf"

        if not input_str and req.pubchem_cid:
            # Look up SMILES for PubChem CID
            import httpx
            url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{req.pubchem_cid}/property/CanonicalSMILES/JSON"
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    props = res.json().get("PropertyTable", {}).get("Properties", [])
                    if props:
                        input_str = props[0].get("CanonicalSMILES")
                        input_type = "smiles"

        if not input_str:
            msg = "Valid SMILES string, SDF text, or PubChem CID must be provided."
            raise ValueError(msg)

        _, _, meta = prepare_ligand(input_str, input_type=input_type)

        return LigandPrepResponse(
            name=req.name or f"Ligand {meta['formula']}",
            formula=meta["formula"],
            molecular_weight=meta["molecular_weight"],
            num_heavy_atoms=meta["num_heavy_atoms"],
            num_rotatable_bonds=meta["num_rotatable_bonds"],
            canonical_smiles=meta["canonical_smiles"],
            warnings=[],
        )

    async def detect_pocket_coordinates(self, req: PocketDetectRequest) -> BoundingBox:
        """Detect binding pocket from co-crystallized ligand or amino acid residue list."""
        pdb_text = req.pdb_text
        if not pdb_text and req.pdb_id:
            pdb_text = await self.structure_client.get_rcsb_pdb_text(req.pdb_id.strip().upper())

        if not pdb_text:
            msg = "Valid PDB coordinates are required to detect pocket."
            raise ValueError(msg)

        if req.selected_residues:
            box = detect_pocket_from_residues(pdb_text, req.selected_residues, padding=req.padding)
            if box:
                return box

        box = detect_pocket_from_ligand(pdb_text, ligand_resname=req.ligand_resname, padding=req.padding)
        if box:
            return box

        # Fallback to receptor centroid
        _, _, meta = prepare_receptor(pdb_text)
        c = meta["center_xyz"]
        return BoundingBox(
            center_x=c[0],
            center_y=c[1],
            center_z=c[2],
            size_x=22.0,
            size_y=22.0,
            size_z=22.0,
        )

    # ---------------------------------------------------------
    # 2. Docking Job Submission & Asynchronous Execution
    # ---------------------------------------------------------

    async def submit_job(
        self,
        db: Session,
        req: DockingSubmitRequest,
        user_id: int | None = None,
    ) -> DockingJobResponse:
        """Create a persistent docking job record and dispatch to background worker."""
        # 1. Resolve receptor PDB
        pdb_text = req.protein_pdb_text
        if not pdb_text and req.protein_source == "pdb":
            pdb_text = await self.structure_client.get_rcsb_pdb_text(req.protein_id.strip().upper())
        elif not pdb_text and req.protein_source == "alphafold":
            alpha_meta = await self.structure_client.get_alphafold_prediction(req.protein_id.strip().upper())
            if alpha_meta and alpha_meta.get("pdb_url"):
                import httpx
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.get(alpha_meta["pdb_url"])
                    if resp.status_code == 200:
                        pdb_text = resp.text

        if not pdb_text:
            msg = f"Failed to acquire protein coordinates for {req.protein_id}"
            raise ValueError(msg)

        # 2. Resolve ligand input
        lig_input = req.ligand_input or req.ligand_id
        if not lig_input:
            msg = "Ligand input (SMILES, CID, or structure text) is required"
            raise ValueError(msg)

        # 3. Prepare molecules to validate syntax before queueing
        clean_pdb, rec_pdbqt, _ = prepare_receptor(pdb_text)
        lig_pdbqt, _, _lig_meta = prepare_ligand(lig_input)

        # 4. Create persistent database record
        job_id = str(uuid.uuid4())
        job = DockingJob(
            id=job_id,
            user_id=user_id,
            project_id=req.project_id,
            name=req.name,
            status="QUEUED",
            protein_name=req.protein_id,
            protein_source=req.protein_source,
            ligand_name=req.ligand_id,
            ligand_source=req.ligand_source,
            binding_pocket=req.binding_pocket.model_dump(),
            docking_config=req.docking_config.model_dump(),
            created_at=datetime.now(UTC),
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        # 5. Dispatch background execution
        _executor.submit(
            self._execute_docking_background,
            job_id,
            clean_pdb,
            rec_pdbqt,
            lig_pdbqt,
            req.binding_pocket,
            req.docking_config,
        )

        return self._format_job_response(job)

    def _execute_docking_background(
        self,
        job_id: str,
        receptor_pdb: str,
        receptor_pdbqt: str,
        ligand_pdbqt: str,
        pocket: BoundingBox,
        config: DockingConfig,
    ) -> None:
        """Worker thread task executing AutoDock Vina, interaction profiling, and DB update."""
        db = SessionLocal()
        try:
            job = db.scalar(select(DockingJob).where(DockingJob.id == job_id))
            if not job:
                logger.error("Job %s not found in worker thread", job_id)
                return

            job.status = "RUNNING"
            db.commit()

            # Execute AutoDock Vina
            poses_data, log_output, exec_time = run_autodock_vina(
                receptor_pdbqt=receptor_pdbqt,
                ligand_pdbqt=ligand_pdbqt,
                pocket=pocket,
                config=config,
            )

            # Analyze interactions for each pose
            best_score = None
            for p in poses_data:
                mode_num = p["mode_number"]
                affinity = p["affinity_kcal_mol"]
                if best_score is None or affinity < best_score:
                    best_score = affinity

                # Interaction analysis
                interaction = analyze_pose_interactions(
                    receptor_pdb=receptor_pdb,
                    docked_pose_pdb=p["pdb_block"],
                    mode_number=mode_num,
                    affinity_kcal_mol=affinity,
                )

                pose_record = DockingPose(
                    job_id=job.id,
                    mode_number=mode_num,
                    affinity_kcal_mol=affinity,
                    rmsd_lower_bound=p["rmsd_lower_bound"],
                    rmsd_upper_bound=p["rmsd_upper_bound"],
                    pdb_block=p["pdb_block"],
                    contacts=[c.model_dump() for c in interaction.contacts],
                    hbond_count=interaction.hydrogen_bonds_count,
                    hydrophobic_count=interaction.hydrophobic_contacts_count,
                    salt_bridge_count=interaction.salt_bridges_count,
                )
                db.add(pose_record)

            # Save receptor PDB to storage directory for reference
            storage_dir = Path("storage/docking")
            storage_dir.mkdir(parents=True, exist_ok=True)
            rec_file = storage_dir / f"{job_id}_receptor.pdb"
            with open(rec_file, "w", encoding="utf-8") as f:
                f.write(receptor_pdb)

            job.receptor_storage_path = str(rec_file)
            job.best_affinity = best_score
            job.execution_time_seconds = exec_time
            job.log_output = log_output
            job.status = "COMPLETED"
            job.completed_at = datetime.now(UTC)
            db.commit()
            logger.info("Docking job %s completed in %.2fs. Best affinity: %.2f kcal/mol", job_id, exec_time, best_score or 0.0)

        except Exception as exc:
            logger.exception("Docking job %s failed during execution", job_id)
            db.rollback()
            try:
                job = db.scalar(select(DockingJob).where(DockingJob.id == job_id))
                if job:
                    job.status = "FAILED"
                    job.error_message = str(exc)
                    job.completed_at = datetime.now(UTC)
                    db.commit()
            except Exception as inner_exc:  # noqa: BLE001
                logger.error("Failed to update failed job status: %s", inner_exc)
        finally:
            db.close()

    # ---------------------------------------------------------
    # 3. Querying Jobs & Details
    # ---------------------------------------------------------

    def get_job_detail(
        self,
        db: Session,
        job_id: str,
        user_id: int | None = None,
    ) -> DockingJobDetailResponse | None:
        """Fetch full job details including ranked poses, interactions, and receptor coordinates."""
        query = select(DockingJob).where(DockingJob.id == job_id)
        if user_id is not None:
            query = query.where((DockingJob.user_id == user_id) | (DockingJob.user_id.is_(None)))
        else:
            query = query.where(DockingJob.user_id.is_(None))

        job = db.scalar(query)
        if not job:
            return None

        # Load receptor PDB
        rec_pdb = None
        if job.receptor_storage_path and os.path.exists(job.receptor_storage_path):
            with open(job.receptor_storage_path, encoding="utf-8") as f:
                rec_pdb = f.read()

        pose_responses = [
            DockingPoseResponse(
                id=p.id,
                mode_number=p.mode_number,
                affinity_kcal_mol=p.affinity_kcal_mol,
                rmsd_lower_bound=p.rmsd_lower_bound,
                rmsd_upper_bound=p.rmsd_upper_bound,
                pdb_block=p.pdb_block,
                hbond_count=p.hbond_count,
                hydrophobic_count=p.hydrophobic_count,
                salt_bridge_count=p.salt_bridge_count,
                contacts=[InteractionContact(**c) for c in (p.contacts or [])],
            )
            for p in job.poses
        ]

        base = self._format_job_response(job)
        return DockingJobDetailResponse(
            **base.model_dump(),
            poses=pose_responses,
            receptor_pdb=rec_pdb,
            log_output=job.log_output,
        )

    def list_jobs(
        self,
        db: Session,
        user_id: int | None = None,
        limit: int = 50,
    ) -> list[DockingJobResponse]:
        """List past docking jobs with strict user data isolation."""
        query = select(DockingJob)
        if user_id is not None:
            query = query.where((DockingJob.user_id == user_id) | (DockingJob.user_id.is_(None)))
        else:
            query = query.where(DockingJob.user_id.is_(None))
        query = query.order_by(DockingJob.created_at.desc()).limit(limit)

        jobs = db.scalars(query).all()
        return [self._format_job_response(j) for j in jobs]

    @staticmethod
    def reconcile_interrupted_jobs(db: Session) -> int:
        """Find any docking jobs left in QUEUED or RUNNING states upon server restart and mark them as failed."""
        interrupted = db.scalars(
            select(DockingJob).where(DockingJob.status.in_(["QUEUED", "RUNNING"]))
        ).all()
        for j in interrupted:
            j.status = "FAILED"
            j.error_message = "Docking computation was interrupted by a backend server restart. Please resubmit."
            j.completed_at = datetime.now(UTC)
        if interrupted:
            db.commit()
            logger.info("Reconciled %d interrupted docking jobs on startup", len(interrupted))
        return len(interrupted)

    def _format_job_response(self, job: DockingJob) -> DockingJobResponse:
        return DockingJobResponse(
            id=job.id,
            name=job.name,
            status=job.status,
            protein_name=job.protein_name,
            protein_source=job.protein_source,
            ligand_name=job.ligand_name,
            ligand_source=job.ligand_source,
            binding_pocket=BoundingBox(**job.binding_pocket),
            docking_config=DockingConfig(**job.docking_config),
            best_affinity=job.best_affinity,
            execution_time_seconds=job.execution_time_seconds,
            error_message=job.error_message,
            created_at=job.created_at,
            completed_at=job.completed_at,
        )

    # ---------------------------------------------------------
    # 4. Backward-Compatible Legacy Methods
    # ---------------------------------------------------------

    async def get_pdb_ligands(self, pdb_id: str) -> PdbLigandsResponse:
        """Extract all bound non-water hetero-molecule ligands from a PDB structure."""
        clean_id = pdb_id.strip().upper()
        pdb_text = await self.structure_client.get_rcsb_pdb_text(clean_id)
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
        """Legacy 3D atomic interaction analysis preserved for backward compatibility."""
        clean_id = pdb_id.strip().upper()
        pdb_text = await self.structure_client.get_rcsb_pdb_text(clean_id)
        if not pdb_text:
            return None

        parser = PDBParser(QUIET=True)
        structure = parser.get_structure(clean_id, io.StringIO(pdb_text))
        first_model = next(structure.get_models(), None)
        if not first_model:
            return None

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

        protein_atoms = []
        for chain in first_model.get_chains():
            for residue in chain.get_residues():
                if residue.id[0] == " ":
                    for atom in residue.get_atoms():
                        protein_atoms.append((chain.id, residue, atom))

        contacts: list[InteractionContact] = []
        pocket_residues_set: set[str] = set()
        ligand_coords = []
        h_bonds_count = 0
        hydrophobic_count = 0
        salt_bridges_count = 0

        for l_chain, _, l_atom in ligand_atoms:
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

                    itype = "van_der_waals"
                    if dist <= 3.5 and l_element in POLAR_H_BOND_ATOMS and p_element in POLAR_H_BOND_ATOMS:
                        itype = "hydrogen_bond"
                        h_bonds_count += 1
                    elif dist <= 4.0 and l_element == "C" and p_element == "C" and p_resname in HYDROPHOBIC_RESIDUES:
                        itype = "hydrophobic"
                        hydrophobic_count += 1
                    elif dist <= 4.0 and (
                        (p_resname in CHARGED_BASIC and l_element in ("O", "S", "P"))
                        or (p_resname in CHARGED_ACIDIC and l_element == "N")
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
                            protein_coord=[round(float(c), 3) for c in p_coord],
                            ligand_coord=[round(float(c), 3) for c in l_coord],
                        )
                    )

        contacts.sort(key=lambda c: c.distance_angstroms)
        coords_arr = np.array(ligand_coords)
        center = np.mean(coords_arr, axis=0).tolist()
        radius = float(np.max(np.linalg.norm(coords_arr - center, axis=1))) + max_distance
        volume_estimate = round((4.0 / 3.0) * math.pi * (radius**3), 2)

        vdw_count = max(0, len(contacts) - h_bonds_count - hydrophobic_count - salt_bridges_count)
        delta_g = round(-0.6 * h_bonds_count - 0.8 * salt_bridges_count - 0.25 * hydrophobic_count - 0.08 * vdw_count, 2)
        binding_score = round(min(100.0, max(10.0, abs(delta_g) * 6.5 + len(contacts) * 0.5)), 1)

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
            contacts=contacts[:100],
        )
