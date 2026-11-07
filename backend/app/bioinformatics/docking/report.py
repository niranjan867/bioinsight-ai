from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.schemas.reports import GenerateReportRequest, ReportSection

if TYPE_CHECKING:
    from app.bioinformatics.docking.schemas import DockingJobDetailResponse

logger = logging.getLogger(__name__)


def build_docking_report_request(
    job: DockingJobDetailResponse,
    author_name: str | None = None,
) -> GenerateReportRequest:
    """Build a publication-ready GenerateReportRequest from a completed DockingJobDetailResponse."""
    author = author_name or "BioInsight AI Research Suite"
    title = f"Molecular Docking Study: {job.ligand_name} with {job.protein_name}"
    subtitle = f"AutoDock Vina In Silico Binding Profile & Interaction Analysis (Job: {job.id[:8]})"

    best_eff = (
        f"{job.best_affinity:.2f} kcal/mol"
        if job.best_affinity is not None
        else "N/A"
    )

    summary = (
        f"In silico molecular docking simulation was conducted between target macromolecule "
        f"'{job.protein_name}' (Source: {job.protein_source}) and chemical ligand '{job.ligand_name}' "
        f"(Source: {job.ligand_source}) utilizing native AutoDock Vina v1.2.5. "
        f"The search space bounding box was centered at "
        f"({job.binding_pocket.center_x:.2f}, {job.binding_pocket.center_y:.2f}, {job.binding_pocket.center_z:.2f}) Å "
        f"with dimensions {job.binding_pocket.size_x:.1f} × {job.binding_pocket.size_y:.1f} × {job.binding_pocket.size_z:.1f} Å "
        f"(exhaustiveness = {job.docking_config.exhaustiveness}). "
        f"The simulation yielded {len(job.poses)} ranked conformational binding modes. "
        f"The primary predicted mode demonstrated a binding free energy of {best_eff}, "
        f"with key non-covalent stabilizing contacts identified across the target active site."
    )

    sections: list[ReportSection] = []

    # Section 1: Parameters Table
    runtime_str = f"{job.execution_time_seconds:.2f} s" if job.execution_time_seconds else "N/A"
    param_table = [
        ["Parameter", "Configured Value", "Description / Metric"],
        ["Target Receptor", job.protein_name, f"Source: {job.protein_source}"],
        ["Ligand Compound", job.ligand_name, f"Source: {job.ligand_source}"],
        [
            "Grid Center (X, Y, Z)",
            f"({job.binding_pocket.center_x:.2f}, {job.binding_pocket.center_y:.2f}, {job.binding_pocket.center_z:.2f}) Å",
            "Target active site centroid",
        ],
        [
            "Grid Dimensions",
            f"{job.binding_pocket.size_x:.1f} × {job.binding_pocket.size_y:.1f} × {job.binding_pocket.size_z:.1f} Å",
            "3D search space volume",
        ],
        ["Search Exhaustiveness", str(job.docking_config.exhaustiveness), "Global optimization thoroughness"],
        ["Conformations Evaluated", str(len(job.poses)), "Ranked binding poses generated"],
        ["Energy Range Window", f"{job.docking_config.energy_range} kcal/mol", "Maximum delta from top pose"],
        ["Execution Runtime", runtime_str, f"Status: {job.status.upper()}"],
    ]
    sections.append(
        ReportSection(
            title="1. Search Space & Docking Configuration",
            content=(
                "AutoDock Vina uses an iterated local search global optimizer with the Vina empirical "
                "scoring function. The search space definition dictates the active site boundary within which "
                "ligand rotatable bonds and rigid-body degrees of freedom are evaluated."
            ),
            table_data=param_table,
        )
    )

    # Section 2: Ranked Poses Table
    pose_table: list[list[str]] = [
        ["Mode", "Affinity (kcal/mol)", "RMSD l.b. (Å)", "RMSD u.b. (Å)", "H-Bonds", "Hydrophobic", "Salt Bridges"],
    ]
    for pose in job.poses:
        pose_table.append([
            f"Mode {pose.mode_number}",
            f"{pose.affinity_kcal_mol:.2f}",
            f"{pose.rmsd_lower_bound:.2f}",
            f"{pose.rmsd_upper_bound:.2f}",
            str(pose.hbond_count),
            str(pose.hydrophobic_count),
            str(pose.salt_bridge_count),
        ])

    sections.append(
        ReportSection(
            title="2. Ranked Binding Affinity Poses",
            content=(
                "Ranked conformations predicted by AutoDock Vina scoring function. More negative scores indicate "
                "thermodynamically favorable binding free energy (kcal/mol). RMSD values reflect structural deviation "
                "relative to the top-ranked mode."
            ),
            table_data=pose_table if len(job.poses) > 0 else None,
        )
    )

    # Section 3: Interaction Profile for Pose 1
    top_pose = job.poses[0] if job.poses else None
    if top_pose and top_pose.contacts:
        contacts_table: list[list[str]] = [
            ["Residue", "Chain", "Interaction Type", "Distance (Å)", "Ligand Atom", "Receptor Atom"],
        ]
        # Display up to 25 contacts
        for contact in top_pose.contacts[:25]:
            c_type = contact.interaction_type.replace("_", " ").title()
            contacts_table.append([
                f"{contact.residue_name} {contact.residue_number}",
                contact.chain_id or "A",
                c_type,
                f"{contact.distance:.2f}",
                contact.atom_ligand or "-",
                contact.atom_receptor or "-",
            ])
        sections.append(
            ReportSection(
                title="3. Active Site Interaction Profile (Mode 1)",
                content=(
                    f"Detailed interatomic contacts identified within 4.0 Å between the top-scoring ligand pose "
                    f"and target binding pocket residues. Identified {top_pose.hbond_count} hydrogen bonds, "
                    f"{top_pose.hydrophobic_count} hydrophobic contacts, and {top_pose.salt_bridge_count} salt bridges."
                ),
                table_data=contacts_table,
            )
        )
    else:
        sections.append(
            ReportSection(
                title="3. Active Site Interaction Profile",
                content=(
                    "No specific non-covalent contacts were identified within the 4.0 Å interaction distance "
                    "threshold for the evaluated poses."
                ),
            )
        )

    # Section 4: Methodology
    sections.append(
        ReportSection(
            title="4. Computational Methodology",
            content=(
                "Receptor coordinates were preprocessed using Biopython to strip solvent water molecules, "
                "filter alternate crystallographic conformations, and verify atomic chains. Ligand 3D conformers "
                "were generated from SMILES representations using RDKit's ETKDGv3 distance geometry method, "
                "energy-minimized with the Universal Force Field (UFF), assigned empirical Gasteiger partial charges, "
                "and formatted into PDBQT format with Meeko. Docking simulations were performed natively with the "
                "Scripps AutoDock Vina v1.2.5 engine. 3D contact geometries were analyzed using Euclidean distance "
                "criteria (Hydrogen bonds ≤ 3.5 Å, Salt bridges ≤ 4.0 Å, Hydrophobic contacts ≤ 4.0 Å)."
            ),
        )
    )

    # Section 5: Disclaimer
    sections.append(
        ReportSection(
            title="5. Scientific & Regulatory Notice",
            content=(
                "NOTICE: AutoDock Vina predicted binding affinities are empirical computational estimates "
                "of binding free energy and do not represent experimentally verified thermodynamic parameters "
                "(e.g., Kd, Ki, or IC50). This report is generated strictly for academic and biopharmaceutical "
                "research hypothesis generation and does not constitute clinical validation or regulatory "
                "evidence. Experimental biochemical assays are required to confirm biological efficacy."
            ),
        )
    )

    references = [
        "Trott O, Olson AJ. AutoDock Vina: improving the speed and accuracy of docking with a new scoring function, efficient optimization, and multithreading. J Comput Chem. 2010;31(2):455-461.",
        "Eberhardt J, Santos-Martins D, Tillack AF, Forli S. AutoDock Vina 1.2.0: New Docking Methods, Expanded Force Field, and Python Bindings. J Chem Inf Model. 2021;61(8):3891-3898.",
        "Landrum G, et al. RDKit: Open-source cheminformatics and machine learning. https://www.rdkit.org",
        "Forli S, et al. Computational protein-ligand docking and virtual drug screening with the AutoDock suite. Nat Protoc. 2016;11(5):905-919.",
        "Cock PA, et al. Biopython: freely available Python tools for computational molecular biology and bioinformatics. Bioinformatics. 2009;25(11):1422-1423.",
    ]

    return GenerateReportRequest(
        title=title,
        subtitle=subtitle,
        author_name=author,
        summary=summary,
        sections=sections,
        references=references,
    )
