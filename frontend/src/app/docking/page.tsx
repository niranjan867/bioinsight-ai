"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import Script from "next/script";
import {
  Crosshair,
  Layers,
  Atom,
  Play,
  RotateCw,
  CheckCircle2,
  AlertTriangle,
  History,
  Box,
  Eye,
  Info,
  Sparkles,
  Download,
  FileText,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { apiRequest, getApiBaseUrl } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { Viewer3D } from "@/types/3dmol";

interface BoundingBox {
  center_x: number;
  center_y: number;
  center_z: number;
  size_x: number;
  size_y: number;
  size_z: number;
}

interface InteractionContact {
  chain_id: string;
  residue_name: string;
  residue_number: number;
  atom_name: string;
  ligand_atom_name: string;
  distance_angstroms: number;
  interaction_type: string;
  protein_coord: number[];
  ligand_coord: number[];
}

interface DockingPose {
  id: number;
  mode_number: number;
  affinity_kcal_mol: number;
  rmsd_lower_bound: number;
  rmsd_upper_bound: number;
  pdb_block: string;
  hbond_count: number;
  hydrophobic_count: number;
  salt_bridge_count: number;
  contacts: InteractionContact[];
}

interface DockingJobDetail {
  id: string;
  name: string;
  status: string;
  protein_name: string;
  protein_source: string;
  ligand_name: string;
  ligand_source: string;
  binding_pocket: BoundingBox;
  best_affinity?: number | null;
  execution_time_seconds?: number | null;
  error_message?: string | null;
  created_at: string;
  completed_at?: string | null;
  poses: DockingPose[];
  receptor_pdb?: string | null;
  log_output?: string | null;
  scientific_disclaimer: string;
}

interface DockingJobSummary {
  id: string;
  name: string;
  status: string;
  protein_name: string;
  ligand_name: string;
  best_affinity?: number | null;
  execution_time_seconds?: number | null;
  created_at: string;
}

export default function MolecularDockingPage() {
  const [activeTab, setActiveTab] = useState("workbench");

  // Step 1: Target Protein
  const [proteinSource, setProteinSource] = useState<"pdb" | "uniprot" | "alphafold">("pdb");
  const [proteinId, setProteinId] = useState("4HHB");
  const [receptorPdbText, setReceptorPdbText] = useState<string | null>(null);
  const [isPreppingProtein, setIsPreppingProtein] = useState(false);
  const [proteinChains, setProteinChains] = useState<string[]>([]);
  const [detectedLigands, setDetectedLigands] = useState<Array<{ chemical_id: string; chain_id: string; atom_count: number }>>([]);

  // Step 2: Ligand
  const [ligandSource, setLigandSource] = useState<"smiles" | "pubchem">("smiles");
  const [ligandInput, setLigandInput] = useState("CC(=O)Oc1ccccc1C(=O)O"); // Aspirin
  const [ligandName, setLigandName] = useState("Aspirin");
  const [ligandFormula, setLigandFormula] = useState<string | null>(null);
  const [ligandMW, setLigandMW] = useState<number | null>(null);
  const [isPreppingLigand, setIsPreppingLigand] = useState(false);

  // Step 3: Binding Pocket
  const [pocketMode, setPocketMode] = useState<"ligand" | "residues" | "manual">("manual");
  const [selectedResiduesStr, setSelectedResiduesStr] = useState("HIS146, LYS40");
  const [box, setBox] = useState<BoundingBox>({
    center_x: 24.0,
    center_y: 25.0,
    center_z: 2.0,
    size_x: 20.0,
    size_y: 20.0,
    size_z: 20.0,
  });

  // Step 4: Execution & Parameters
  const [jobName, setJobName] = useState("Aspirin Docking to 4HHB");
  const [exhaustiveness, setExhaustiveness] = useState(8);
  const [numModes, setNumModes] = useState(9);
  const [isExecuting, setIsExecuting] = useState(false);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string | null>(null);
  const [activeJobDetail, setActiveJobDetail] = useState<DockingJobDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Step 5: Visualization & Poses
  const [selectedPoseIndex, setSelectedPoseIndex] = useState(0);
  const [scriptLoaded, setScriptLoaded] = useState(false);
  const viewerContainerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<Viewer3D | null>(null);
  const [showPocketBox, setShowPocketBox] = useState(true);
  const [showInteractions, setShowInteractions] = useState(true);

  // History Tab
  const { token } = useAuth();
  const [historyJobs, setHistoryJobs] = useState<DockingJobSummary[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [isDownloadingReport, setIsDownloadingReport] = useState(false);

  const handleDownloadReport = async (jobId: string, format: "pdf" | "docx" = "pdf") => {
    setIsDownloadingReport(true);
    try {
      const baseUrl = getApiBaseUrl();
      const headers: Record<string, string> = {};
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
      const res = await fetch(`${baseUrl}/api/v1/docking/jobs/${jobId}/report?format=${format}`, {
        headers,
      });
      if (!res.ok) {
        const errJson = await res.json().catch(() => null);
        throw new Error(errJson?.detail || `Failed to download report (${res.status})`);
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `docking_report_${jobId.slice(0, 8)}.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Report generation failed");
    } finally {
      setIsDownloadingReport(false);
    }
  };

  const loadHistory = async () => {
    setIsLoadingHistory(true);
    try {
      const list = await apiRequest<DockingJobSummary[]>("/api/v1/docking/jobs?limit=25");
      setHistoryJobs(list);
    } catch (err) {
      console.error("History fetch error", err);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const fetchReceptorData = async (targetId: string) => {
    setIsPreppingProtein(true);
    setError(null);
    try {
      const res = await apiRequest<{
        atom_count: number;
        residue_count: number;
        chains: string[];
        detected_ligands: Array<{ chemical_id: string; chain_id: string; atom_count: number }>;
        suggested_box: BoundingBox;
      }>("/api/v1/docking/prepare/receptor", {
        method: "POST",
        body: JSON.stringify({ pdb_id: targetId, remove_water: true }),
      });

      setProteinChains(res.chains);
      setDetectedLigands(res.detected_ligands);
      if (res.suggested_box) {
        setBox(res.suggested_box);
      }

      // Also get raw PDB text for visualization
      const rawText = await apiRequest<string>(`/api/v1/structures/${targetId}/pdb`);
      setReceptorPdbText(rawText);
    } catch (err: unknown) {
      console.error(err);
    } finally {
      setIsPreppingProtein(false);
    }
  };

  useEffect(() => {
    let ignore = false;
    async function loadInitial() {
      try {
        const [prepRes, rawText, historyList] = await Promise.all([
          apiRequest<{
            atom_count: number;
            residue_count: number;
            chains: string[];
            detected_ligands: Array<{ chemical_id: string; chain_id: string; atom_count: number }>;
            suggested_box: BoundingBox;
          }>("/api/v1/docking/prepare/receptor", {
            method: "POST",
            body: JSON.stringify({ pdb_id: "4HHB", remove_water: true }),
          }),
          apiRequest<string>("/api/v1/structures/4HHB/pdb"),
          apiRequest<DockingJobSummary[]>("/api/v1/docking/jobs?limit=25"),
        ]);
        if (!ignore) {
          setProteinChains(prepRes.chains);
          setDetectedLigands(prepRes.detected_ligands);
          if (prepRes.suggested_box) setBox(prepRes.suggested_box);
          setReceptorPdbText(rawText);
          setHistoryJobs(historyList);
        }
      } catch (err) {
        console.error("Docking initial load error", err);
      }
    }
    loadInitial();
    return () => {
      ignore = true;
    };
  }, []);

  const handlePrepareLigand = async () => {
    setIsPreppingLigand(true);
    try {
      const payload = ligandSource === "smiles"
        ? { smiles: ligandInput, name: ligandName }
        : { pubchem_cid: ligandInput, name: ligandName };

      const res = await apiRequest<{
        formula: string;
        molecular_weight: number;
        canonical_smiles: string;
        num_rotatable_bonds: number;
      }>("/api/v1/docking/prepare/ligand", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      setLigandFormula(res.formula);
      setLigandMW(res.molecular_weight);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Ligand prep failed";
      setError(msg);
    } finally {
      setIsPreppingLigand(false);
    }
  };

  const handleDetectPocket = async () => {
    if (!receptorPdbText) return;
    try {
      const payload: { pdb_text: string; selected_residues?: string[]; ligand_resname?: string } = {
        pdb_text: receptorPdbText,
      };

      if (pocketMode === "residues") {
        payload.selected_residues = selectedResiduesStr.split(",").map((s) => s.trim());
      } else if (pocketMode === "ligand" && detectedLigands.length > 0) {
        payload.ligand_resname = detectedLigands[0].chemical_id;
      }

      const resBox = await apiRequest<BoundingBox>("/api/v1/docking/pocket", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      setBox(resBox);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Pocket detection failed";
      setError(msg);
    }
  };

  const handleLaunchDocking = async () => {
    setIsExecuting(true);
    setError(null);
    setJobStatus("QUEUED");

    try {
      const payload = {
        name: jobName,
        protein_source: proteinSource,
        protein_id: proteinId,
        protein_pdb_text: receptorPdbText,
        ligand_source: ligandSource,
        ligand_id: ligandName,
        ligand_input: ligandInput,
        binding_pocket: box,
        docking_config: {
          exhaustiveness,
          num_modes: numModes,
          energy_range: 3.0,
          scoring: "vina",
        },
      };

      const res = await apiRequest<{ id: string; status: string }>("/api/v1/docking/jobs", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      setActiveJobId(res.id);
      pollJobStatus(res.id);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Submission failed";
      setError(msg);
      setIsExecuting(false);
    }
  };

  const pollJobStatus = async (jobId: string) => {
    const check = async () => {
      try {
        const detail = await apiRequest<DockingJobDetail>(`/api/v1/docking/jobs/${jobId}`);
        setJobStatus(detail.status);

        if (detail.status === "COMPLETED") {
          setActiveJobDetail(detail);
          setIsExecuting(false);
          setSelectedPoseIndex(0);
          loadHistory();
          return;
        }

        if (detail.status === "FAILED") {
          setIsExecuting(false);
          setError(detail.error_message || "AutoDock Vina execution failed");
          return;
        }

        setTimeout(check, 1500);
      } catch (err) {
        console.error("Polling error", err);
        setIsExecuting(false);
      }
    };
    check();
  };

  const loadPastJob = async (jobId: string) => {
    try {
      const detail = await apiRequest<DockingJobDetail>(`/api/v1/docking/jobs/${jobId}`);
      setActiveJobDetail(detail);
      setActiveJobId(detail.id);
      setSelectedPoseIndex(0);
      if (detail.receptor_pdb) {
        setReceptorPdbText(detail.receptor_pdb);
      }
      setBox(detail.binding_pocket);
      setActiveTab("workbench");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load past job";
      setError(msg);
    }
  };

  // -------------------------------------------------------------
  // 3D Visualization Pipeline (3Dmol.js)
  // -------------------------------------------------------------
  useEffect(() => {
    if (!scriptLoaded || !viewerContainerRef.current || !window.$3Dmol) return;

    if (!viewerRef.current) {
      viewerRef.current = window.$3Dmol.createViewer(viewerContainerRef.current, {
        backgroundColor: "0x090d16",
      });
    }

    const viewer = viewerRef.current;
    viewer.clear();

    // 1. Render Protein Receptor
    const proteinPdb = activeJobDetail?.receptor_pdb || receptorPdbText;
    if (proteinPdb) {
      viewer.addModel(proteinPdb, "pdb");
      viewer.setStyle({ hetflag: false }, { cartoon: { color: "spectrum", opacity: 0.85 } });
    }

    // 2. Render Selected Docked Pose
    const selectedPose = activeJobDetail?.poses?.[selectedPoseIndex];
    if (selectedPose?.pdb_block) {
      viewer.addModel(selectedPose.pdb_block, "pdb");
      viewer.setStyle({ resn: "UNL" }, { stick: { colorscheme: "cyanCarbon", radius: 0.25 } });
      viewer.setStyle({ resn: "LIG" }, { stick: { colorscheme: "cyanCarbon", radius: 0.25 } });

      // 3. Render 3D Interaction Contact Lines
      if (showInteractions && selectedPose.contacts) {
        selectedPose.contacts.forEach((c) => {
          let lineColor = "0xeab308"; // Yellow for H-bonds
          if (c.interaction_type === "hydrophobic") lineColor = "0x06b6d4"; // Cyan
          if (c.interaction_type === "salt_bridge") lineColor = "0xf97316"; // Orange

          viewer.addLine({
            start: { x: c.protein_coord[0], y: c.protein_coord[1], z: c.protein_coord[2] },
            end: { x: c.ligand_coord[0], y: c.ligand_coord[1], z: c.ligand_coord[2] },
            dashed: true,
            color: lineColor,
          });

          // Highlight and label interacting residue
          viewer.addStyle(
            { resi: c.residue_number, chain: c.chain_id },
            { stick: { colorscheme: "whiteCarbon", radius: 0.12 } }
          );
        });
      }
    }

    // 4. Render Bounding Box Wireframe
    if (showPocketBox && box) {
      const minX = box.center_x - box.size_x / 2;
      const maxX = box.center_x + box.size_x / 2;
      const minY = box.center_y - box.size_y / 2;
      const maxY = box.center_y + box.size_y / 2;
      const minZ = box.center_z - box.size_z / 2;
      const maxZ = box.center_z + box.size_z / 2;

      const corners = [
        [minX, minY, minZ], [maxX, minY, minZ], [maxX, maxY, minZ], [minX, maxY, minZ],
        [minX, minY, maxZ], [maxX, minY, maxZ], [maxX, maxY, maxZ], [minX, maxY, maxZ],
      ];

      const edges = [
        [0, 1], [1, 2], [2, 3], [3, 0],
        [4, 5], [5, 6], [6, 7], [7, 4],
        [0, 4], [1, 5], [2, 6], [3, 7],
      ];

      edges.forEach(([i, j]) => {
        viewer.addLine({
          start: { x: corners[i][0], y: corners[i][1], z: corners[i][2] },
          end: { x: corners[j][0], y: corners[j][1], z: corners[j][2] },
          color: "0xa855f7", // Purple wireframe
        });
      });
    }

    viewer.zoomTo();
    viewer.render();
  }, [scriptLoaded, receptorPdbText, activeJobDetail, selectedPoseIndex, showPocketBox, showInteractions, box]);

  const currentPose = activeJobDetail?.poses?.[selectedPoseIndex];

  return (
    <div className="container mx-auto space-y-6 p-4 md:p-6 max-w-7xl">
      <Script
        src="https://cdnjs.cloudflare.com/ajax/libs/3Dmol/2.4.2/3Dmol-min.js"
        onLoad={() => setScriptLoaded(true)}
      />

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b pb-5">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-3 py-0.5 text-xs font-semibold text-primary">
            <Crosshair className="h-3.5 w-3.5" />
            AutoDock Vina Engine
          </div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight">
            Molecular Docking Workbench
          </h1>
          <p className="text-xs text-muted-foreground">
            Genuine protein-ligand docking with RDKit conformer generation, Meeko torsion mapping,
            geometric interaction profiling, and interactive 3D visualization.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href="/databases"
            className="inline-flex items-center gap-1.5 rounded-md border border-input bg-background px-3 py-1.5 text-xs font-medium hover:bg-accent hover:text-accent-foreground h-9"
          >
            <Layers className="h-3.5 w-3.5" />
            Database Hub
          </Link>
          {activeJobDetail && (
            <div className="flex items-center gap-1.5">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleDownloadReport(activeJobDetail.id, "pdf")}
                disabled={isDownloadingReport}
                className="gap-1.5 text-xs h-9"
              >
                <Download className="h-3.5 w-3.5 text-primary" />
                {isDownloadingReport ? "Generating..." : "PDF Report"}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleDownloadReport(activeJobDetail.id, "docx")}
                disabled={isDownloadingReport}
                className="text-xs h-9"
                title="Download Word Document"
              >
                DOCX
              </Button>
            </div>
          )}
          <Link
            href="/reports"
            className="inline-flex items-center gap-1.5 rounded-md border border-input bg-background px-3 py-1.5 text-xs font-medium hover:bg-accent hover:text-accent-foreground h-9"
          >
            <FileText className="h-3.5 w-3.5" />
            All Reports
          </Link>
        </div>
      </div>

      {/* Error alert */}
      {error && (
        <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-3.5 text-xs text-destructive flex items-center gap-3">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <div className="flex-1">{error}</div>
          <Button variant="ghost" size="sm" className="h-6 text-[11px]" onClick={() => setError(null)}>
            Dismiss
          </Button>
        </div>
      )}

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-2 max-w-md">
          <TabsTrigger value="workbench" className="gap-2 text-xs">
            <Crosshair className="h-3.5 w-3.5" />
            Docking Workbench
          </TabsTrigger>
          <TabsTrigger value="history" className="gap-2 text-xs">
            <History className="h-3.5 w-3.5" />
            Docking History ({historyJobs.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="workbench" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Control Column (Steps 1 to 4) */}
            <div className="lg:col-span-5 space-y-5">
              {/* Step 1: Target Protein Selection */}
              <Card>
                <CardHeader className="py-3 px-4 border-b bg-muted/30">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                      <Layers className="h-3.5 w-3.5 text-primary" />
                      1. Target Protein Receptor
                    </CardTitle>
                    {isPreppingProtein && <RotateCw className="h-3.5 w-3.5 animate-spin text-primary" />}
                  </div>
                </CardHeader>
                <CardContent className="p-4 space-y-3 text-xs">
                  <div className="grid grid-cols-3 gap-2">
                    <div className="col-span-1">
                      <select
                        value={proteinSource}
                        onChange={(e) => setProteinSource(e.target.value as "pdb" | "uniprot" | "alphafold")}
                        className="h-8 text-xs w-full rounded-md border border-input bg-background px-2"
                      >
                        <option value="pdb">RCSB PDB</option>
                        <option value="uniprot">UniProt</option>
                        <option value="alphafold">AlphaFold</option>
                      </select>
                    </div>
                    <div className="col-span-2 flex gap-1.5">
                      <Input
                        value={proteinId}
                        onChange={(e) => setProteinId(e.target.value)}
                        placeholder="PDB ID or Accession"
                        className="h-8 text-xs font-mono"
                      />
                      <Button
                        size="sm"
                        variant="secondary"
                        className="h-8 text-xs shrink-0"
                        onClick={() => fetchReceptorData(proteinId)}
                        disabled={isPreppingProtein}
                      >
                        Fetch & Prep
                      </Button>
                    </div>
                  </div>

                  {proteinChains.length > 0 && (
                    <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
                      <span>Chains: <strong className="text-foreground">{proteinChains.join(", ")}</strong></span>
                      {detectedLigands.length > 0 && (
                        <span>• Bound Ligands: <strong className="text-foreground">{detectedLigands.map((l) => l.chemical_id).join(", ")}</strong></span>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Step 2: Ligand Selection */}
              <Card>
                <CardHeader className="py-3 px-4 border-b bg-muted/30">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                      <Atom className="h-3.5 w-3.5 text-primary" />
                      2. Ligand Molecule
                    </CardTitle>
                    {isPreppingLigand && <RotateCw className="h-3.5 w-3.5 animate-spin text-primary" />}
                  </div>
                </CardHeader>
                <CardContent className="p-4 space-y-3 text-xs">
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-[11px] font-medium text-muted-foreground">Ligand Name</label>
                      <Input
                        value={ligandName}
                        onChange={(e) => setLigandName(e.target.value)}
                        className="h-8 text-xs mt-1"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] font-medium text-muted-foreground">Format</label>
                      <select
                        value={ligandSource}
                        onChange={(e) => setLigandSource(e.target.value as "smiles" | "pubchem")}
                        className="h-8 text-xs mt-1 w-full rounded-md border border-input bg-background px-2"
                      >
                        <option value="smiles">SMILES String</option>
                        <option value="pubchem">PubChem CID</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="text-[11px] font-medium text-muted-foreground">
                      {ligandSource === "smiles" ? "SMILES Structure" : "PubChem Compound ID"}
                    </label>
                    <div className="flex gap-2 mt-1">
                      <Input
                        value={ligandInput}
                        onChange={(e) => setLigandInput(e.target.value)}
                        placeholder="e.g. CC(=O)Oc1ccccc1C(=O)O"
                        className="h-8 text-xs font-mono"
                      />
                      <Button
                        size="sm"
                        variant="secondary"
                        className="h-8 text-xs shrink-0"
                        onClick={handlePrepareLigand}
                        disabled={isPreppingLigand}
                      >
                        Validate 3D
                      </Button>
                    </div>
                  </div>

                  {ligandFormula && (
                    <div className="flex items-center gap-2 text-[11px] text-muted-foreground bg-muted/40 p-2 rounded-md">
                      <span>Formula: <strong className="text-foreground">{ligandFormula}</strong></span>
                      <span>• MW: <strong className="text-foreground">{ligandMW} g/mol</strong></span>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Step 3: Binding Pocket Selection */}
              <Card>
                <CardHeader className="py-3 px-4 border-b bg-muted/30">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                      <Box className="h-3.5 w-3.5 text-primary" />
                      3. Binding Pocket Search Space
                    </CardTitle>
                    <Button size="sm" variant="ghost" className="h-6 text-[10px] px-1.5" onClick={handleDetectPocket}>
                      Auto-Detect
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="p-4 space-y-3 text-xs">
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-[10px] text-muted-foreground">Pocket Method</label>
                      <select
                        value={pocketMode}
                        onChange={(e) => setPocketMode(e.target.value as "ligand" | "residues" | "manual")}
                        className="h-7 text-xs w-full rounded-md border border-input bg-background px-2 mt-1"
                      >
                        <option value="manual">Manual Bounding Box</option>
                        <option value="ligand">Co-Crystallized Ligand</option>
                        <option value="residues">Residue List</option>
                      </select>
                    </div>
                    {pocketMode === "residues" && (
                      <div>
                        <label className="text-[10px] text-muted-foreground">Residues (e.g. HIS146, LYS40)</label>
                        <Input
                          value={selectedResiduesStr}
                          onChange={(e) => setSelectedResiduesStr(e.target.value)}
                          className="h-7 text-xs font-mono mt-1"
                        />
                      </div>
                    )}
                  </div>

                  <div className="grid grid-cols-3 gap-2">
                    <div>
                      <label className="text-[10px] text-muted-foreground">Center X (Å)</label>
                      <Input
                        type="number"
                        value={box.center_x}
                        onChange={(e) => setBox({ ...box, center_x: parseFloat(e.target.value) || 0 })}
                        className="h-7 text-xs font-mono"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-muted-foreground">Center Y (Å)</label>
                      <Input
                        type="number"
                        value={box.center_y}
                        onChange={(e) => setBox({ ...box, center_y: parseFloat(e.target.value) || 0 })}
                        className="h-7 text-xs font-mono"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-muted-foreground">Center Z (Å)</label>
                      <Input
                        type="number"
                        value={box.center_z}
                        onChange={(e) => setBox({ ...box, center_z: parseFloat(e.target.value) || 0 })}
                        className="h-7 text-xs font-mono"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2">
                    <div>
                      <label className="text-[10px] text-muted-foreground">Size X (Å)</label>
                      <Input
                        type="number"
                        value={box.size_x}
                        onChange={(e) => setBox({ ...box, size_x: parseFloat(e.target.value) || 20 })}
                        className="h-7 text-xs font-mono"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-muted-foreground">Size Y (Å)</label>
                      <Input
                        type="number"
                        value={box.size_y}
                        onChange={(e) => setBox({ ...box, size_y: parseFloat(e.target.value) || 20 })}
                        className="h-7 text-xs font-mono"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-muted-foreground">Size Z (Å)</label>
                      <Input
                        type="number"
                        value={box.size_z}
                        onChange={(e) => setBox({ ...box, size_z: parseFloat(e.target.value) || 20 })}
                        className="h-7 text-xs font-mono"
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Step 4: Execution Configuration */}
              <Card className="border-primary/20 bg-primary/5">
                <CardHeader className="py-3 px-4 border-b">
                  <CardTitle className="text-xs font-bold uppercase tracking-wider text-primary flex items-center gap-2">
                    <Play className="h-3.5 w-3.5 text-primary" />
                    4. AutoDock Vina Execution
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-4 space-y-4 text-xs">
                  <div>
                    <label className="text-[11px] font-medium text-muted-foreground">Job Title</label>
                    <Input
                      value={jobName}
                      onChange={(e) => setJobName(e.target.value)}
                      className="h-8 text-xs mt-1"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-[11px] font-medium text-muted-foreground">Exhaustiveness ({exhaustiveness})</label>
                      <input
                        type="range"
                        min="1"
                        max="24"
                        value={exhaustiveness}
                        onChange={(e) => setExhaustiveness(parseInt(e.target.value))}
                        className="w-full mt-2"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] font-medium text-muted-foreground">Max Poses ({numModes})</label>
                      <input
                        type="range"
                        min="1"
                        max="20"
                        value={numModes}
                        onChange={(e) => setNumModes(parseInt(e.target.value))}
                        className="w-full mt-2"
                      />
                    </div>
                  </div>

                  <Button
                    onClick={handleLaunchDocking}
                    disabled={isExecuting}
                    className="w-full h-10 gap-2 text-xs font-semibold shadow-xs"
                  >
                    {isExecuting ? (
                      <>
                        <RotateCw className="h-4 w-4 animate-spin" />
                        Executing AutoDock Vina ({jobStatus || "PROCESSING"})...
                      </>
                    ) : (
                      <>
                        <Play className="h-4 w-4" />
                        Run AutoDock Vina Docking
                      </>
                    )}
                  </Button>

                  {jobStatus && (
                    <div className="flex items-center justify-between text-[11px] px-2 py-1 bg-background/80 rounded border">
                      <span className="text-muted-foreground">
                        {activeJobId ? `Job ${activeJobId.slice(0, 8)}...` : "Status:"}
                      </span>
                      <Badge variant={jobStatus === "COMPLETED" ? "default" : "secondary"} className="text-[10px]">
                        {jobStatus}
                      </Badge>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Right Visualization & Results Column */}
            <div className="lg:col-span-7 space-y-5">
              {/* 3D Molecular Viewer Card */}
              <Card className="overflow-hidden">
                <CardHeader className="py-2.5 px-4 border-b bg-card flex flex-row items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                      <Eye className="h-3.5 w-3.5 text-primary" />
                      Interactive 3D Docking Viewer
                    </CardTitle>
                    {currentPose && (
                      <Badge variant="outline" className="text-[10px] font-mono">
                        Pose {currentPose.mode_number} ({currentPose.affinity_kcal_mol} kcal/mol)
                      </Badge>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant={showPocketBox ? "secondary" : "ghost"}
                      className="h-7 text-[11px] px-2 gap-1"
                      onClick={() => setShowPocketBox(!showPocketBox)}
                    >
                      <Box className="h-3 w-3" />
                      Box
                    </Button>
                    <Button
                      size="sm"
                      variant={showInteractions ? "secondary" : "ghost"}
                      className="h-7 text-[11px] px-2 gap-1"
                      onClick={() => setShowInteractions(!showInteractions)}
                    >
                      <Sparkles className="h-3 w-3" />
                      Contacts
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  <div
                    ref={viewerContainerRef}
                    className="w-full h-[450px] relative bg-[#090d16]"
                  >
                    {!scriptLoaded && (
                      <div className="absolute inset-0 flex items-center justify-center text-xs text-muted-foreground">
                        <RotateCw className="h-5 w-5 animate-spin mr-2" />
                        Initializing WebGL 3D molecular canvas...
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Ranked Poses & Interactions Table */}
              {activeJobDetail && activeJobDetail.poses.length > 0 && (
                <Card>
                  <CardHeader className="py-3 px-4 border-b">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                        Ranked Poses & Calculated Vina Affinities ({activeJobDetail.poses.length})
                      </CardTitle>
                      <div className="flex items-center gap-2">
                        <span className="text-[11px] text-muted-foreground mr-1">
                          Completed in {activeJobDetail.execution_time_seconds}s
                        </span>
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-7 text-xs px-2.5 gap-1.5"
                          onClick={() => handleDownloadReport(activeJobDetail.id, "pdf")}
                          disabled={isDownloadingReport}
                        >
                          <Download className="h-3 w-3 text-primary" />
                          PDF Report
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-7 text-xs px-2.5 gap-1.5"
                          onClick={() => handleDownloadReport(activeJobDetail.id, "docx")}
                          disabled={isDownloadingReport}
                        >
                          <Download className="h-3 w-3" />
                          DOCX
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="p-0">
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs text-left">
                        <thead className="bg-muted/50 border-b text-[11px] text-muted-foreground">
                          <tr>
                            <th className="py-2 px-3">Mode</th>
                            <th className="py-2 px-3">Affinity (kcal/mol)</th>
                            <th className="py-2 px-3">RMSD l.b. (Å)</th>
                            <th className="py-2 px-3">RMSD u.b. (Å)</th>
                            <th className="py-2 px-3">H-Bonds</th>
                            <th className="py-2 px-3">Hydrophobic</th>
                            <th className="py-2 px-3">Action</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y font-mono">
                          {activeJobDetail.poses.map((pose, idx) => (
                            <tr
                              key={pose.id}
                              onClick={() => setSelectedPoseIndex(idx)}
                              className={`cursor-pointer transition-colors ${
                                selectedPoseIndex === idx ? "bg-primary/10 font-bold" : "hover:bg-muted/30"
                              }`}
                            >
                              <td className="py-2 px-3">Pose {pose.mode_number}</td>
                              <td className="py-2 px-3 text-emerald-600 font-semibold">{pose.affinity_kcal_mol}</td>
                              <td className="py-2 px-3">{pose.rmsd_lower_bound}</td>
                              <td className="py-2 px-3">{pose.rmsd_upper_bound}</td>
                              <td className="py-2 px-3 text-amber-500">{pose.hbond_count}</td>
                              <td className="py-2 px-3 text-cyan-500">{pose.hydrophobic_count}</td>
                              <td className="py-2 px-3">
                                <Button
                                  size="sm"
                                  variant={selectedPoseIndex === idx ? "default" : "outline"}
                                  className="h-6 text-[10px] px-2 font-sans"
                                >
                                  {selectedPoseIndex === idx ? "Viewing" : "View 3D"}
                                </Button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Interacting Residues Details */}
              {currentPose && currentPose.contacts.length > 0 && (
                <Card>
                  <CardHeader className="py-2.5 px-4 border-b">
                    <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                      <Sparkles className="h-3.5 w-3.5 text-primary" />
                      Interacting Binding Residues (Pose {currentPose.mode_number})
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-3">
                    <div className="flex flex-wrap gap-1.5">
                      {Array.from(new Set(currentPose.contacts.map((c) => `${c.residue_name}${c.residue_number}:${c.chain_id}`))).map((res) => (
                        <Badge key={res} variant="outline" className="text-xs font-mono bg-muted/30">
                          {res}
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Scientific Disclaimer */}
              <div className="p-3 rounded-xl border border-muted bg-muted/20 text-[11px] text-muted-foreground flex items-start gap-2.5">
                <Info className="h-4 w-4 shrink-0 text-muted-foreground mt-0.5" />
                <p>
                  <strong>Scientific Notice:</strong> AutoDock Vina scores are empirical computational estimates of binding free energy
                  (kcal/mol), not experimentally measured dissociation constants (Ki/Kd/IC50). Biological binding and activity must be validated experimentally.
                </p>
              </div>
            </div>
          </div>
        </TabsContent>

        {/* Tab 2: Docking History */}
        <TabsContent value="history">
          <Card>
            <CardHeader className="py-4 px-6 border-b">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base font-bold">Docking Job History</CardTitle>
                  <CardDescription className="text-xs">
                    Persistent database archive of all molecular docking runs and AutoDock Vina logs.
                  </CardDescription>
                </div>
                <Button size="sm" variant="outline" onClick={loadHistory} disabled={isLoadingHistory} className="gap-1.5 text-xs h-8">
                  <RotateCw className={`h-3.5 w-3.5 ${isLoadingHistory ? "animate-spin" : ""}`} />
                  Refresh
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              {historyJobs.length === 0 ? (
                <div className="text-center py-16 text-muted-foreground text-xs">
                  No previous docking jobs found in this project workspace.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-muted/40 border-b text-[11px] text-muted-foreground">
                      <tr>
                        <th className="py-2.5 px-4">Job Name</th>
                        <th className="py-2.5 px-4">Protein Receptor</th>
                        <th className="py-2.5 px-4">Ligand</th>
                        <th className="py-2.5 px-4">Status</th>
                        <th className="py-2.5 px-4">Best Affinity</th>
                        <th className="py-2.5 px-4">Run Time</th>
                        <th className="py-2.5 px-4">Date</th>
                        <th className="py-2.5 px-4 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {historyJobs.map((job) => (
                        <tr key={job.id} className="hover:bg-muted/20 transition-colors">
                          <td className="py-2.5 px-4 font-semibold text-foreground">{job.name}</td>
                          <td className="py-2.5 px-4 font-mono">{job.protein_name}</td>
                          <td className="py-2.5 px-4">{job.ligand_name}</td>
                          <td className="py-2.5 px-4">
                            <Badge
                              variant={job.status === "COMPLETED" ? "default" : job.status === "FAILED" ? "destructive" : "secondary"}
                              className="text-[10px]"
                            >
                              {job.status}
                            </Badge>
                          </td>
                          <td className="py-2.5 px-4 font-mono font-semibold text-emerald-600">
                            {job.best_affinity !== null && job.best_affinity !== undefined
                              ? `${job.best_affinity} kcal/mol`
                              : "—"}
                          </td>
                          <td className="py-2.5 px-4 font-mono text-muted-foreground">
                            {job.execution_time_seconds ? `${job.execution_time_seconds}s` : "—"}
                          </td>
                          <td className="py-2.5 px-4 text-muted-foreground">
                            {new Date(job.created_at).toLocaleDateString()}
                          </td>
                          <td className="py-2.5 px-4 text-right">
                            <div className="flex items-center justify-end gap-1.5">
                              {job.status === "COMPLETED" && (
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  className="h-7 text-xs px-2 gap-1 text-muted-foreground hover:text-foreground"
                                  title="Download PDF Report"
                                  onClick={() => handleDownloadReport(job.id, "pdf")}
                                  disabled={isDownloadingReport}
                                >
                                  <Download className="h-3.5 w-3.5" />
                                  PDF
                                </Button>
                              )}
                              <Button
                                size="sm"
                                variant="outline"
                                className="h-7 text-xs px-2.5 gap-1"
                                onClick={() => loadPastJob(job.id)}
                              >
                                <Eye className="h-3.5 w-3.5" />
                                Inspect
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
