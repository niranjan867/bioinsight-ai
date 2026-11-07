"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import Script from "next/script";
import {
  Layers,
  Search,
  Download,
  RotateCw,
  Plus,
  Check,
  AlertCircle,
  Crosshair,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { apiRequest, getApiBaseUrl } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { Viewer3D } from "@/types/3dmol";

interface BoundLigand {
  chemical_id: string;
  name: string;
  formula: string | null;
  chain_id: string | null;
}

interface StructureMetadata {
  structure_id: string;
  title: string;
  experimental_method: string;
  resolution: number | null;
  release_date: string | null;
  is_experimental: boolean;
  bound_ligands: BoundLigand[];
  chains: string[];
  total_residues: number;
  total_atoms: number;
  source: string;
  retrieved_at: string;
}

interface AlphaFoldMetadata {
  uniprot_accession: string;
  entry_id: string;
  gene_symbol: string | null;
  organism: string;
  global_plddt: number;
  confidence_category: string;
  model_url: string;
  pdb_url: string;
  cif_url: string;
  is_experimental: boolean;
  source: string;
}

interface ProjectSummary {
  id: number;
  name: string;
}

export default function StructuresPage() {
  const { user } = useAuth();
  const [query, setQuery] = useState("4HHB");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [structureMeta, setStructureMeta] = useState<StructureMetadata | null>(null);
  const [alphaFoldMeta, setAlphaFoldMeta] = useState<AlphaFoldMetadata | null>(null);
  const [rawPdbText, setRawPdbText] = useState<string | null>(null);

  // 3Dmol viewer state
  const viewerContainerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<Viewer3D | null>(null);
  const [styleMode, setStyleMode] = useState<"cartoon" | "stick" | "surface" | "sphere">("cartoon");
  const [colorMode, setColorMode] = useState<"spectrum" | "chain" | "ss">("spectrum");
  const [isSpinning, setIsSpinning] = useState(false);
  const [scriptLoaded, setScriptLoaded] = useState(false);

  // Save to project modal
  const [saveModalOpen, setSaveModalOpen] = useState(false);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [isSavingToProject, setIsSavingToProject] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const fetchStructure = async (idToFetch: string) => {
    const cleanId = idToFetch.trim();
    if (!cleanId) return;

    setIsLoading(true);
    setError(null);
    setStructureMeta(null);
    setAlphaFoldMeta(null);
    setRawPdbText(null);

    try {
      if (cleanId.length === 4 && cleanId.match(/^[a-zA-Z0-9]{4}$/)) {
        // Experimental PDB ID
        const meta = await apiRequest<StructureMetadata>(`/api/v1/structures/${cleanId}`);
        setStructureMeta(meta);

        // Fetch PDB text
        const baseUrl = getApiBaseUrl();
        const res = await fetch(`${baseUrl}/api/v1/structures/${cleanId}/pdb`);
        if (res.ok) {
          const text = await res.text();
          setRawPdbText(text);
        }
      } else {
        // Try AlphaFold UniProt accession (e.g. P68871)
        const afMeta = await apiRequest<AlphaFoldMetadata>(`/api/v1/structures/alphafold/${cleanId}`);
        setAlphaFoldMeta(afMeta);

        // Fetch AlphaFold PDB text
        const baseUrl = getApiBaseUrl();
        const res = await fetch(`${baseUrl}/api/v1/structures/${cleanId}/pdb`);
        if (res.ok) {
          const text = await res.text();
          setRawPdbText(text);
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to load macromolecular 3D structure.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    let ignore = false;
    async function loadInitial() {
      try {
        const meta = await apiRequest<StructureMetadata>("/api/v1/structures/4HHB");
        if (!ignore) {
          setStructureMeta(meta);
          const baseUrl = getApiBaseUrl();
          const res = await fetch(`${baseUrl}/api/v1/structures/4HHB/pdb`);
          if (res.ok) {
            const text = await res.text();
            setRawPdbText(text);
          }
        }
      } catch (err: unknown) {
        if (!ignore && err instanceof Error) {
          setError(err.message);
        }
      }
    }
    loadInitial();
    return () => {
      ignore = true;
    };
  }, []);

  // Initialize or update 3Dmol viewer whenever PDB text, styleMode, or colorMode changes
  useEffect(() => {
    if (!scriptLoaded || !rawPdbText || !viewerContainerRef.current || !window.$3Dmol) {
      return;
    }

    try {
      const container = viewerContainerRef.current;
      container.innerHTML = "";
      const viewer = window.$3Dmol.createViewer(container, {
        backgroundColor: "white",
      });
      viewerRef.current = viewer;

      viewer.addModel(rawPdbText, "pdb");

      let styleConfig: Record<string, unknown> = {};
      if (styleMode === "cartoon") {
        styleConfig = { cartoon: { color: colorMode } };
      } else if (styleMode === "stick") {
        styleConfig = { stick: { radius: 0.15, colorscheme: "Jmol" } };
      } else if (styleMode === "sphere") {
        styleConfig = { sphere: { radius: 0.8, colorscheme: "Jmol" } };
      } else if (styleMode === "surface") {
        styleConfig = { cartoon: { color: colorMode } };
        viewer.addSurface(1, { opacity: 0.65, color: colorMode });
      }

      viewer.setStyle({}, styleConfig);

      // Highlight bound ligands if any with thicker stick representation
      viewer.setStyle({ hetflag: true }, { stick: { colorscheme: "greenCarbon", radius: 0.3 } });

      viewer.zoomTo();
      viewer.render();
    } catch (err) {
      console.warn("3Dmol rendering error:", err);
    }
  }, [scriptLoaded, rawPdbText, styleMode, colorMode]);

  // Toggle rotation
  useEffect(() => {
    if (!viewerRef.current) return;
    viewerRef.current.spin(isSpinning);
  }, [isSpinning]);

  const handleDownloadPdb = () => {
    if (!rawPdbText) return;
    const blob = new Blob([rawPdbText], { type: "chemical/x-pdb" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${(structureMeta?.structure_id || alphaFoldMeta?.entry_id || "structure").toLowerCase()}.pdb`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  const openSaveDialog = async () => {
    if (!user) {
      alert("Please sign in to save entities to your research projects.");
      return;
    }
    setSaveModalOpen(true);
    setSaveSuccess(false);
    try {
      const projs = await apiRequest<ProjectSummary[]>("/api/v1/projects");
      setProjects(projs);
      if (projs.length > 0) setSelectedProjectId(projs[0].id);
    } catch {
      setProjects([]);
    }
  };

  const handleSaveToProject = async () => {
    if (!selectedProjectId) return;
    const currentId = structureMeta?.structure_id || alphaFoldMeta?.uniprot_accession;
    const currentTitle = structureMeta?.title || `AlphaFold model for ${alphaFoldMeta?.gene_symbol || alphaFoldMeta?.uniprot_accession}`;
    if (!currentId) return;

    setIsSavingToProject(true);
    try {
      await apiRequest(`/api/v1/projects/${selectedProjectId}/items`, {
        method: "POST",
        body: {
          item_type: "structure",
          item_id: currentId,
          title: currentTitle,
          description: structureMeta
            ? `Experimental ${structureMeta.experimental_method} (${structureMeta.resolution ? `${structureMeta.resolution} Å` : "Structure"})`
            : `AlphaFold Computational Prediction (pLDDT: ${alphaFoldMeta?.global_plddt})`,
          metadata_json: {
            is_experimental: structureMeta ? structureMeta.is_experimental : false,
            chains: structureMeta?.chains || [],
            plddt: alphaFoldMeta?.global_plddt,
          },
        },
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveModalOpen(false), 1200);
    } catch (err: unknown) {
      if (err instanceof Error) alert(err.message);
    } finally {
      setIsSavingToProject(false);
    }
  };

  return (
    <>
      {/* Dynamic 3Dmol script loader */}
      <Script
        src="https://cdnjs.cloudflare.com/ajax/libs/3Dmol/2.4.2/3Dmol-min.js"
        strategy="lazyOnload"
        onLoad={() => setScriptLoaded(true)}
      />

      <div className="space-y-6 p-6 md:p-8">
        {/* Header */}
        <div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="border-indigo-500/30 text-indigo-500 text-[10px]">
              <Layers className="mr-1 h-3 w-3" />
              Structural Biology
            </Badge>
            <span className="text-xs text-muted-foreground">RCSB PDB & AlphaFold DB</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-foreground">
            Protein Structure Explorer
          </h1>
          <p className="text-xs text-muted-foreground">
            Explore 3D atomic structures, verify experimental resolutions, inspect AlphaFold confidence, and examine bound ligands
          </p>
        </div>

        {/* Search Bar & Quick Queries */}
        <Card className="border-border/80 bg-card shadow-xs">
          <CardContent className="pt-5 space-y-3">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                fetchStructure(query);
              }}
              className="flex gap-2"
            >
              <div className="relative flex-1">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  type="text"
                  placeholder="Enter 4-letter PDB ID (e.g. 4HHB, 1CRN, 1IEP) or UniProt accession (e.g. P68871, P04637)..."
                  className="pl-9 text-xs"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
              </div>
              <Button type="submit" size="sm" className="h-9 text-xs font-semibold gap-1.5" disabled={isLoading || !query.trim()}>
                <Search className="h-3.5 w-3.5" />
                <span>{isLoading ? "Retrieving..." : "Load Structure"}</span>
              </Button>
            </form>

            <div className="flex flex-wrap items-center gap-1.5 text-xs">
              <span className="text-[11px] text-muted-foreground">Sample entries:</span>
              {[
                { label: "Deoxyhemoglobin (4HHB)", id: "4HHB" },
                { label: "Crambin (1CRN)", id: "1CRN" },
                { label: "Abl Kinase + Imatinib (1IEP)", id: "1IEP" },
                { label: "AlphaFold P53 (P04637)", id: "P04637" },
                { label: "AlphaFold Hemoglobin (P68871)", id: "P68871" },
              ].map((sample) => (
                <button
                  key={sample.id}
                  type="button"
                  onClick={() => {
                    setQuery(sample.id);
                    fetchStructure(sample.id);
                  }}
                  className="rounded-md border border-border bg-muted/40 px-2 py-0.5 text-[11px] text-foreground hover:bg-muted transition-colors"
                >
                  {sample.label}
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        {error && (
          <div className="flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Main Workspace: 3D Viewer Canvas & Metadata Panel */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Left Column: Structure Metadata, Polymers, Bound Ligands */}
          <div className="space-y-4 lg:col-span-1">
            <Card className="border-border/80 bg-card shadow-xs">
              <CardHeader className="pb-3 border-b border-border/60">
                <div className="flex items-center justify-between">
                  {structureMeta ? (
                    <Badge className="bg-blue-500/10 text-blue-600 border-blue-500/20 text-[10px] font-bold">
                      Experimental PDB
                    </Badge>
                  ) : alphaFoldMeta ? (
                    <Badge className="bg-purple-500/10 text-purple-600 border-purple-500/20 text-[10px] font-bold">
                      AlphaFold Prediction
                    </Badge>
                  ) : null}

                  <div className="flex items-center gap-1.5">
                    {structureMeta?.resolution && (
                      <Badge variant="outline" className="text-[10px]">
                        {structureMeta.resolution} Å
                      </Badge>
                    )}
                    {alphaFoldMeta && (
                      <Badge variant="outline" className="text-[10px]">
                        pLDDT: {alphaFoldMeta.global_plddt}
                      </Badge>
                    )}
                  </div>
                </div>

                <CardTitle className="text-base font-bold text-foreground mt-2">
                  {structureMeta?.structure_id || alphaFoldMeta?.entry_id}
                </CardTitle>
                <CardDescription className="text-xs leading-relaxed">
                  {structureMeta?.title || `Model for ${alphaFoldMeta?.organism} (${alphaFoldMeta?.gene_symbol || "Target"})`}
                </CardDescription>
              </CardHeader>

              <CardContent className="pt-3.5 space-y-3.5 text-xs">
                {/* Method / Confidence */}
                <div className="rounded-lg bg-muted/20 p-2.5 border border-border/60 space-y-1">
                  <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider block">
                    {structureMeta ? "Determination Method" : "Computational Confidence"}
                  </span>
                  <span className="font-semibold text-foreground">
                    {structureMeta?.experimental_method || alphaFoldMeta?.confidence_category}
                  </span>
                  {structureMeta?.release_date && (
                    <span className="text-[10px] text-muted-foreground block">
                      Deposited: {structureMeta.release_date}
                    </span>
                  )}
                </div>

                {/* Atomic & Chain Stats */}
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="rounded-md border border-border/60 bg-muted/10 p-2">
                    <span className="text-[10px] text-muted-foreground block">Chains</span>
                    <span className="font-bold text-sm text-foreground">
                      {structureMeta?.chains.length || 1}
                    </span>
                  </div>
                  <div className="rounded-md border border-border/60 bg-muted/10 p-2">
                    <span className="text-[10px] text-muted-foreground block">Residues</span>
                    <span className="font-bold text-sm text-foreground">
                      {structureMeta?.total_residues || "—"}
                    </span>
                  </div>
                  <div className="rounded-md border border-border/60 bg-muted/10 p-2">
                    <span className="text-[10px] text-muted-foreground block">Atoms</span>
                    <span className="font-bold text-sm text-foreground">
                      {structureMeta?.total_atoms || "—"}
                    </span>
                  </div>
                </div>

                {/* Bound Ligands in PDB */}
                {structureMeta?.bound_ligands && structureMeta.bound_ligands.length > 0 && (
                  <div className="space-y-1.5">
                    <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider block">
                      Bound Ligands ({structureMeta.bound_ligands.length})
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {structureMeta.bound_ligands.map((lig, idx) => (
                        <Badge key={idx} variant="secondary" className="font-mono text-[10px]">
                          {lig.chemical_id} {lig.chain_id ? `(${lig.chain_id})` : ""}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="pt-2 flex flex-col gap-2">
                  {structureMeta && (
                    <Link href={`/interactions`}>
                      <Button size="sm" className="w-full text-xs font-semibold gap-1.5 bg-primary">
                        <Crosshair className="h-3.5 w-3.5" />
                        <span>Analyze Docking & Binding Site</span>
                      </Button>
                    </Link>
                  )}

                  <div className="grid grid-cols-2 gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={handleDownloadPdb}
                      disabled={!rawPdbText}
                      className="text-xs gap-1.5"
                    >
                      <Download className="h-3 w-3" />
                      <span>Download PDB</span>
                    </Button>

                    <Button
                      size="sm"
                      variant="outline"
                      onClick={openSaveDialog}
                      className="text-xs gap-1.5"
                    >
                      <Plus className="h-3 w-3" />
                      <span>Save to Project</span>
                    </Button>
                  </div>
                </div>

                {/* Save Dialog */}
                <Dialog open={saveModalOpen} onOpenChange={setSaveModalOpen}>
                  <DialogContent className="sm:max-w-md">
                    <DialogHeader>
                      <DialogTitle className="text-base font-bold">Save 3D Structure to Project</DialogTitle>
                      <DialogDescription className="text-xs">
                        Save this macromolecular coordinates entry to your project workspace.
                      </DialogDescription>
                    </DialogHeader>
                    <div className="py-4 space-y-3">
                      {projects.length === 0 ? (
                        <p className="text-xs text-muted-foreground">
                          No projects available. Initialize a project first under <Link href="/projects" className="text-primary underline">Projects</Link>.
                        </p>
                      ) : (
                        <div className="space-y-1">
                          <label className="text-xs font-medium">Select Research Project</label>
                          <select
                            className="w-full rounded-md border border-input bg-background p-2 text-xs"
                            value={selectedProjectId || ""}
                            onChange={(e) => setSelectedProjectId(Number(e.target.value))}
                          >
                            {projects.map((p) => (
                              <option key={p.id} value={p.id}>
                                {p.name}
                              </option>
                            ))}
                          </select>
                        </div>
                      )}
                      {saveSuccess && (
                        <div className="flex items-center gap-2 text-xs text-emerald-600 bg-emerald-500/10 p-2.5 rounded-lg border border-emerald-500/20">
                          <Check className="h-4 w-4" />
                          <span>Structure saved to project!</span>
                        </div>
                      )}
                    </div>
                    <DialogFooter>
                      <Button variant="ghost" size="sm" onClick={() => setSaveModalOpen(false)} className="text-xs">
                        Close
                      </Button>
                      <Button size="sm" onClick={handleSaveToProject} disabled={isSavingToProject || projects.length === 0} className="text-xs font-semibold">
                        {isSavingToProject ? "Saving..." : "Confirm Save"}
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </CardContent>
            </Card>
          </div>

          {/* Right Column: 3D WebGL Canvas */}
          <div className="lg:col-span-2 space-y-3">
            <Card className="border-border/80 bg-card overflow-hidden shadow-xs">
              {/* Viewer Control Bar */}
              <div className="flex flex-wrap items-center justify-between border-b border-border/60 bg-muted/30 px-4 py-2.5 gap-2">
                <div className="flex items-center gap-2 text-xs">
                  <span className="font-semibold text-muted-foreground">Style:</span>
                  {(["cartoon", "stick", "surface", "sphere"] as const).map((mode) => (
                    <button
                      key={mode}
                      onClick={() => setStyleMode(mode)}
                      className={`rounded px-2 py-0.5 text-[11px] capitalize font-medium transition-colors ${
                        styleMode === mode
                          ? "bg-primary text-primary-foreground font-semibold"
                          : "bg-background text-muted-foreground border border-border/60 hover:text-foreground"
                      }`}
                    >
                      {mode}
                    </button>
                  ))}
                </div>

                <div className="flex items-center gap-2 text-xs">
                  <span className="font-semibold text-muted-foreground">Color:</span>
                  {(["spectrum", "chain", "ss"] as const).map((color) => (
                    <button
                      key={color}
                      onClick={() => setColorMode(color)}
                      className={`rounded px-2 py-0.5 text-[11px] capitalize font-medium transition-colors ${
                        colorMode === color
                          ? "bg-primary text-primary-foreground font-semibold"
                          : "bg-background text-muted-foreground border border-border/60 hover:text-foreground"
                      }`}
                    >
                      {color === "ss" ? "Secondary" : color}
                    </button>
                  ))}

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setIsSpinning(!isSpinning)}
                    className="h-7 px-2 text-[11px] gap-1 ml-1"
                  >
                    <RotateCw className={`h-3 w-3 ${isSpinning ? "animate-spin text-primary" : ""}`} />
                    <span>{isSpinning ? "Stop Spin" : "Spin"}</span>
                  </Button>
                </div>
              </div>

              {/* 3Dmol WebGL Container */}
              <div className="relative h-[520px] w-full bg-white">
                <div ref={viewerContainerRef} className="h-full w-full" />
                {!scriptLoaded && (
                  <div className="absolute inset-0 flex items-center justify-center bg-background/80 backdrop-blur-xs text-xs text-muted-foreground">
                    Initializing WebGL 3D molecular engine...
                  </div>
                )}
                {isLoading && (
                  <div className="absolute inset-0 flex items-center justify-center bg-background/80 backdrop-blur-xs text-xs text-primary font-medium">
                    Loading atomic coordinate stream...
                  </div>
                )}
                <div className="absolute bottom-2 left-3 text-[10px] text-slate-400 font-mono pointer-events-none select-none">
                  Left click + drag to rotate • Scroll to zoom • Right click to pan
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </>
  );
}
