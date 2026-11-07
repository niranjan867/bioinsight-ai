import logging
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from app.bioinformatics.docking.schemas import BoundingBox, DockingConfig

logger = logging.getLogger(__name__)


class DockingExecutionError(RuntimeError):
    """Raised when AutoDock Vina execution fails or produces invalid output."""


def find_vina_executable() -> str:
    """Locate the AutoDock Vina executable in the backend/bin directory or system PATH."""
    repo_root = Path(__file__).resolve().parents[4]
    candidate_paths = [
        repo_root / "backend" / "bin" / "vina.exe",
        repo_root / "backend" / "bin" / "vina",
        Path("backend/bin/vina.exe"),
        Path("backend/bin/vina"),
    ]

    for p in candidate_paths:
        if p.exists() and os.access(p, os.X_OK):
            return str(p.resolve())

    # Fallback to system PATH
    sys_vina = shutil.which("vina") or shutil.which("vina.exe")
    if sys_vina:
        return sys_vina

    msg = (
        "AutoDock Vina binary not found. Please ensure 'backend/bin/vina.exe' "
        "or 'backend/bin/vina' exists and has execution permissions."
    )
    raise DockingExecutionError(msg)


def pdbqt_pose_to_pdb(pdbqt_lines: list[str]) -> str:
    """Convert an AutoDock Vina docked pose PDBQT block into standard PDB format for 3Dmol.js."""
    pdb_lines: list[str] = []
    for line in pdbqt_lines:
        if line.startswith(("ATOM  ", "HETATM")):
            # Extract standard PDB columns 1-66
            base_line = line[:66].ljust(66)
            # Retain element from right or guess from atom name
            atom_name = line[12:16].strip()
            element = atom_name[0] if not atom_name[0].isdigit() else atom_name[1]
            pdb_line = f"{base_line}          {element:>2s}"
            pdb_lines.append(pdb_line)
    return "\n".join(pdb_lines) + "\nEND\n"


def run_autodock_vina(
    receptor_pdbqt: str,
    ligand_pdbqt: str,
    pocket: BoundingBox,
    config: DockingConfig,
    work_dir: str | None = None,
) -> tuple[list[dict[str, Any]], str, float]:
    """Execute AutoDock Vina with genuine molecular coordinates and parameters.

    Returns:
        (poses_list, stdout_log, execution_time_seconds)
    """
    vina_bin = find_vina_executable()
    temp_dir = work_dir or tempfile.mkdtemp(prefix="bioinsight_docking_")
    os.makedirs(temp_dir, exist_ok=True)

    rec_path = os.path.join(temp_dir, "receptor.pdbqt")
    lig_path = os.path.join(temp_dir, "ligand.pdbqt")
    out_path = os.path.join(temp_dir, "docked_output.pdbqt")

    try:
        with open(rec_path, "w", encoding="utf-8") as f:
            f.write(receptor_pdbqt)

        with open(lig_path, "w", encoding="utf-8") as f:
            f.write(ligand_pdbqt)

        cmd = [
            vina_bin,
            "--receptor", rec_path,
            "--ligand", lig_path,
            "--center_x", str(pocket.center_x),
            "--center_y", str(pocket.center_y),
            "--center_z", str(pocket.center_z),
            "--size_x", str(pocket.size_x),
            "--size_y", str(pocket.size_y),
            "--size_z", str(pocket.size_z),
            "--exhaustiveness", str(config.exhaustiveness),
            "--num_modes", str(config.num_modes),
            "--energy_range", str(config.energy_range),
            "--scoring", config.scoring,
            "--out", out_path,
        ]

        if config.seed is not None:
            cmd.extend(["--seed", str(config.seed)])

        logger.info("Executing AutoDock Vina: %s", " ".join(cmd[:10]))
        start_time = time.perf_counter()

        # Execute Vina with timeout (maximum 180 seconds for safety)
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )

        exec_time = round(time.perf_counter() - start_time, 2)
        combined_log = proc.stdout + ("\nSTDERR:\n" + proc.stderr if proc.stderr else "")

        if proc.returncode != 0:
            logger.error("AutoDock Vina failed (exit code %d):\n%s", proc.returncode, combined_log)
            msg = f"AutoDock Vina failed with exit code {proc.returncode}: {proc.stderr.strip() or proc.stdout.strip()}"
            raise DockingExecutionError(msg)

        if not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
            msg = "AutoDock Vina did not generate an output poses file"
            raise DockingExecutionError(msg)

        with open(out_path, encoding="utf-8") as f:
            output_content = f.read()

        poses = parse_vina_output_pdbqt(output_content)
        return poses, combined_log, exec_time

    finally:
        if not work_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as exc:  # noqa: BLE001
                logger.debug("Cleanup warning for %s: %s", temp_dir, exc)


def parse_vina_output_pdbqt(pdbqt_content: str) -> list[dict[str, Any]]:
    """Parse multi-model PDBQT output into ranked poses with binding affinities and RMSDs."""
    poses: list[dict[str, Any]] = []
    models = pdbqt_content.split("MODEL ")

    for model_block in models[1:]:
        lines = model_block.splitlines()
        model_num_match = re.match(r"^(\d+)", lines[0].strip())
        mode_num = int(model_num_match.group(1)) if model_num_match else len(poses) + 1

        affinity = 0.0
        rmsd_lb = 0.0
        rmsd_ub = 0.0

        for line in lines:
            if "REMARK VINA RESULT:" in line:
                # Format: REMARK VINA RESULT:      -8.4      0.000      0.000
                parts = line.replace("REMARK VINA RESULT:", "").split()
                if len(parts) >= 1:
                    affinity = float(parts[0])
                if len(parts) >= 2:
                    rmsd_lb = float(parts[1])
                if len(parts) >= 3:
                    rmsd_ub = float(parts[2])
                break

        pdb_block = pdbqt_pose_to_pdb(lines)

        poses.append({
            "mode_number": mode_num,
            "affinity_kcal_mol": round(affinity, 3),
            "rmsd_lower_bound": round(rmsd_lb, 3),
            "rmsd_upper_bound": round(rmsd_ub, 3),
            "pdb_block": pdb_block,
            "raw_pdbqt_block": "MODEL " + model_block,
        })

    return poses
