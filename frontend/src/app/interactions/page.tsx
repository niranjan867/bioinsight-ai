"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import Script from "next/script";
import {
  Crosshair,
  Zap,
  Plus,
  Check,
  AlertCircle,
  RotateCw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { apiRequest, getApiBaseUrl } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { Viewer3D } from "@/types/3dmol";

interface InteractionContact {
  chain_id: string;
  residue_name: string;
  residue_number: number;
  atom_name: string;
  ligand_atom_name: string;
  distance_angstroms: number;
  interaction_type: string;
}

interface BindingPocketInfo {
  center_xyz: number[];
  radius_angstroms: number;
  estimated_volume_a3: number;
  pocket_residues: string[];
}

interface DockingAnalysis {
  pdb_id: string;
  ligand_id: string;
  ligand_name: string;
  total_contacts: number;
  hydrogen_bonds_count: number;
  hydrophobic_contacts_count: number;
  salt_bridges_count: number;
  estimated_affinity_kcal_mol: number;
  binding_score: number;
  pocket: BindingPocketInfo;
  contacts: InteractionContact[];
  method: string;
}

interface LigandItem {
  chemical_id: string;
  name: string;
  chain_id: string;
  atom_count: number;
}

interface LigandsResponse {
  pdb_id: string;
  ligands: LigandItem[];
}

interface ProjectSummary {
  id: number;
  name: string;
}

export default function InteractionsPage() {
  const { user } = useAuth();
  const [pdbId, setPdbId] = useState("4HHB");
  const [availableLigands, setAvailableLigands] = useState<LigandItem[]>([]);
  const [selectedLigand, setSelectedLigand] = useState<string>("");
  const [maxDistance, setMaxDistance] = useState<number>(4.0);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<DockingAnalysis | null>(null);
  const [rawPdbText, setRawPdbText] = useState<string | null>(null);

  // 3D viewer state
  const viewerContainerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<Viewer3D | null>(null);
  const [isSpinning, setIsSpinning] = useState(false);
  const [scriptLoaded, setScriptLoaded] = useState(false);

  // Save to project modal
  const [saveModalOpen, setSaveModalOpen] = useState(false);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [isSavingToProject, setIsSavingToProject] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Fetch available ligands whenever PDB ID changes
  const fetchLigandsForPdb = async (targetPdb: string) => {
    try {
      const res = await apiRequest<LigandsResponse>(`/api/v1/docking/ligands/${targetPdb.trim().toUpperCase()}`);
      setAvailableLigands(res.ligands);
      if (res.ligands.length > 0) {
        setSelectedLigand(res.ligands[0].chemical_id);
      } else {
        setSelectedLigand("");
      }
    } catch {
      setAvailableLigands([]);
      setSelectedLigand("");
    }
  };

  const handleRunAnalysis = async (targetPdb: string, ligandCode: string) => {
    if (!targetPdb.trim()) return;
    setIsLoading(true);
    setError(null);
    setAnalysis(null);

    try {
      const cleanPdb = targetPdb.trim().toUpperCase();
      const res = await apiRequest<DockingAnalysis>("/api/v1/docking/analyze", {
        method: "POST",
        body: {
          pdb_id: cleanPdb,
          ligand_id: ligandCode || undefined,
          max_distance: maxDistance,
        },
      });
      setAnalysis(res);

      // Fetch PDB text for 3D visualizer
      const baseUrl = getApiBaseUrl();
      const pdbRes = await fetch(`${baseUrl}/api/v1/structures/${cleanPdb}/pdb`);
      if (pdbRes.ok) {
        const text = await pdbRes.text();
        setRawPdbText(text);
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Binding site analysis failed.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    let ignore = false;
    async function loadInitial() {
      try {
        const cleanPdb = "4HHB";
        const ligandCode = "HEM";
        const [ligRes, analysisRes] = await Promise.all([
          apiRequest<LigandsResponse>(`/api/v1/docking/ligands/${cleanPdb}`),
          apiRequest<DockingAnalysis>("/api/v1/docking/analyze", {
            method: "POST",
            body: { pdb_id: cleanPdb, ligand_id: ligandCode, max_distance: 4.0 },
          }),
        ]);
        if (!ignore) {
          setAvailableLigands(ligRes.ligands);
          setSelectedLigand(ligandCode);
          setAnalysis(analysisRes);

          const baseUrl = getApiBaseUrl();
          const pdbRes = await fetch(`${baseUrl}/api/v1/structures/${cleanPdb}/pdb`);
          if (pdbRes.ok && !ignore) {
            const text = await pdbRes.text();
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

  // Render 3D viewer when PDB and analysis are loaded
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

      // 1. Overall protein in semi-transparent light cartoon
      viewer.setStyle({}, { cartoon: { color: "lightgray", opacity: 0.5 } });

      // 2. Bound ligand highlighted in thick stick representation
      const targetLigandCode = analysis?.ligand_id;
      if (targetLigandCode) {
        viewer.setStyle({ resn: targetLigandCode }, { stick: { colorscheme: "greenCarbon", radius: 0.35 } });
      }

      // 3. Highlight contacting pocket residues
      if (analysis && analysis.pocket.pocket_residues) {
        for (const resStr of analysis.pocket.pocket_residues) {
          // resStr is formatted like 'VAL62:A'
          const parts = resStr.split(":");
          const chainId = parts[1] || "A";
          const resNumMatch = parts[0].match(/\d+/);
          if (resNumMatch) {
            const resi = parseInt(resNumMatch[0], 10);
            viewer.setStyle(
              { chain: chainId, resi },
              { stick: { colorscheme: "cyanCarbon", radius: 0.18 }, cartoon: { color: "#0284c7" } }
            );
          }
        }
      }

      viewer.zoomTo({ resn: targetLigandCode || "HEM" });
      viewer.render();
    } catch (err) {
      console.warn("3Dmol docking visualization error:", err);
    }
  }, [scriptLoaded, rawPdbText, analysis]);

  useEffect(() => {
    if (!viewerRef.current) return;
    viewerRef.current.spin(isSpinning);
  }, [isSpinning]);

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
    if (!selectedProjectId || !analysis) return;
    setIsSavingToProject(true);
    try {
      await apiRequest(`/api/v1/projects/${selectedProjectId}/items`, {
        method: "POST",
        body: {
          item_type: "docking",
          item_id: `${analysis.pdb_id}-${analysis.ligand_id}`,
          title: `Docking: ${analysis.pdb_id} + ${analysis.ligand_id}`,
          description: `Binding Affinity: ${analysis.estimated_affinity_kcal_mol} kcal/mol (Score: ${analysis.binding_score}, ${analysis.total_contacts} contacts)`,
          metadata_json: {
            pdb_id: analysis.pdb_id,
            ligand_id: analysis.ligand_id,
            h_bonds: analysis.hydrogen_bonds_count,
            hydrophobic: analysis.hydrophobic_contacts_count,
            salt_bridges: analysis.salt_bridges_count,
            pocket_volume: analysis.pocket.estimated_volume_a3,
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

  const getContactBadge = (type: string) => {
    switch (type) {
      case "hydrogen_bond":
        return <Badge className="bg-blue-500/10 text-blue-600 border-blue-500/20 text-[10px]">H-Bond</Badge>;
      case "hydrophobic":
        return <Badge className="bg-amber-500/10 text-amber-600 border-amber-500/20 text-[10px]">Hydrophobic</Badge>;
      case "salt_bridge":
        return <Badge className="bg-purple-500/10 text-purple-600 border-purple-500/20 text-[10px]">Salt Bridge</Badge>;
      default:
        return <Badge variant="outline" className="text-[10px]">Van der Waals</Badge>;
    }
  };

  return (
    <>
      <Script
        src="https://cdnjs.cloudflare.com/ajax/libs/3Dmol/2.4.2/3Dmol-min.js"
        strategy="lazyOnload"
        onLoad={() => setScriptLoaded(true)}
      />

      <div className="space-y-6 p-6 md:p-8">
        {/* Header */}
        <div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="border-teal-500/30 text-teal-600 dark:text-teal-400 text-[10px]">
              <Crosshair className="mr-1 h-3 w-3" />
              Biomolecular Docking
            </Badge>
            <span className="text-xs text-muted-foreground">3D Coordinate Distance & Empirical Affinity Scoring</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-foreground">
            Protein-Ligand Interaction Laboratory
          </h1>
          <p className="text-xs text-muted-foreground">
            Analyze atomic contact matrices, detect binding pockets, calculate hydrogen bonds, and compute empirical docking binding affinities
          </p>
        </div>

        {/* Input Form & Parameters */}
        <Card className="border-border/80 bg-card shadow-xs">
          <CardContent className="pt-5 space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 items-end">
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Target PDB ID *
                </label>
                <Input
                  type="text"
                  placeholder="e.g. 4HHB, 1IEP, 3WZE"
                  value={pdbId}
                  onChange={(e) => {
                    const val = e.target.value.toUpperCase();
                    setPdbId(val);
                    if (val.length === 4) fetchLigandsForPdb(val);
                  }}
                  className="text-xs font-mono font-bold uppercase"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Bound Chemical Ligand
                </label>
                {availableLigands.length > 0 ? (
                  <select
                    className="w-full rounded-md border border-input bg-background p-2 text-xs"
                    value={selectedLigand}
                    onChange={(e) => setSelectedLigand(e.target.value)}
                  >
                    {availableLigands.map((lig) => (
                      <option key={`${lig.chemical_id}-${lig.chain_id}`} value={lig.chemical_id}>
                        {lig.chemical_id} (Chain {lig.chain_id}, {lig.atom_count} atoms)
                      </option>
                    ))}
                  </select>
                ) : (
                  <Input
                    type="text"
                    placeholder="e.g. HEM, STI, ATP"
                    value={selectedLigand}
                    onChange={(e) => setSelectedLigand(e.target.value.toUpperCase())}
                    className="text-xs font-mono"
                  />
                )}
              </div>

              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Distance Cutoff: {maxDistance.toFixed(1)} Å
                </label>
                <input
                  type="range"
                  min="2.5"
                  max="6.0"
                  step="0.1"
                  value={maxDistance}
                  onChange={(e) => setMaxDistance(parseFloat(e.target.value))}
                  className="w-full accent-primary"
                />
              </div>

              <Button
                size="sm"
                onClick={() => handleRunAnalysis(pdbId, selectedLigand)}
                disabled={isLoading || !pdbId.trim()}
                className="h-9 text-xs font-semibold gap-1.5"
              >
                <Zap className="h-3.5 w-3.5" />
                <span>{isLoading ? "Calculating..." : "Compute Interactions"}</span>
              </Button>
            </div>
          </CardContent>
        </Card>

        {error && (
          <div className="flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Results Workspace */}
        {analysis && (
          <div className="space-y-6">
            {/* Metric Tiles */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <Card className="border-border/80 bg-card p-4">
                <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground block">
                  Est. Binding Free Energy
                </span>
                <span className="text-2xl font-bold text-primary block mt-0.5">
                  {analysis.estimated_affinity_kcal_mol} <span className="text-xs font-normal text-muted-foreground">kcal/mol</span>
                </span>
                <span className="text-[10px] text-muted-foreground">Empirical force field scoring</span>
              </Card>

              <Card className="border-border/80 bg-card p-4">
                <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground block">
                  Interaction Quality Score
                </span>
                <span className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 block mt-0.5">
                  {analysis.binding_score} <span className="text-xs font-normal text-muted-foreground">/ 100</span>
                </span>
                <span className="text-[10px] text-muted-foreground">Contact density & H-bond index</span>
              </Card>

              <Card className="border-border/80 bg-card p-4">
                <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground block">
                  Hydrogen Bonds
                </span>
                <span className="text-2xl font-bold text-blue-600 dark:text-blue-400 block mt-0.5">
                  {analysis.hydrogen_bonds_count}
                </span>
                <span className="text-[10px] text-muted-foreground">Polar contacts ≤ 3.5 Å</span>
              </Card>

              <Card className="border-border/80 bg-card p-4">
                <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground block">
                  Pocket Volume
                </span>
                <span className="text-2xl font-bold text-foreground block mt-0.5">
                  {analysis.pocket.estimated_volume_a3} <span className="text-xs font-normal text-muted-foreground">Å³</span>
                </span>
                <span className="text-[10px] text-muted-foreground">{analysis.pocket.pocket_residues.length} binding residues</span>
              </Card>
            </div>

            {/* Two-Column: 3D Pocket Visualization + Contact Table */}
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              {/* Left Column: 3D Pocket Canvas */}
              <Card className="border-border/80 bg-card overflow-hidden shadow-xs flex flex-col justify-between">
                <div className="flex items-center justify-between border-b border-border/60 bg-muted/30 px-4 py-2 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-foreground">Pocket Center:</span>
                    <span className="font-mono text-[11px] text-muted-foreground">
                      [{analysis.pocket.center_xyz.join(", ")}]
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setIsSpinning(!isSpinning)}
                      className="h-7 px-2 text-[11px] gap-1"
                    >
                      <RotateCw className={`h-3 w-3 ${isSpinning ? "animate-spin text-primary" : ""}`} />
                      <span>{isSpinning ? "Stop" : "Spin"}</span>
                    </Button>
                    <Button
                      size="sm"
                      variant="default"
                      onClick={openSaveDialog}
                      className="h-7 px-2.5 text-[11px] gap-1 font-semibold"
                    >
                      <Plus className="h-3 w-3" />
                      <span>Save to Project</span>
                    </Button>
                  </div>
                </div>

                <div className="relative h-[440px] w-full bg-white">
                  <div ref={viewerContainerRef} className="h-full w-full" />
                  <div className="absolute bottom-2 left-3 text-[10px] text-slate-400 font-mono pointer-events-none select-none">
                    Green = Ligand ({analysis.ligand_id}) • Cyan = Active Pocket Residues
                  </div>
                </div>
              </Card>

              {/* Right Column: Contact Table */}
              <Card className="border-border/80 bg-card shadow-xs">
                <CardHeader className="pb-3 border-b border-border/60">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-sm font-bold">Intermolecular Contact Matrix</CardTitle>
                      <CardDescription className="text-xs">
                        Top {analysis.contacts.length} contacting atomic pairs within {maxDistance} Å
                      </CardDescription>
                    </div>
                    <Badge variant="outline" className="text-[10px]">
                      {analysis.total_contacts} Contacts
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="pt-3">
                  <div className="max-h-[380px] overflow-y-auto rounded-lg border border-border/60">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-muted/50 text-[10px] uppercase tracking-wider text-muted-foreground border-b border-border/60 sticky top-0">
                        <tr>
                          <th className="px-3 py-2 font-semibold">Residue</th>
                          <th className="px-3 py-2 font-semibold">Protein Atom</th>
                          <th className="px-3 py-2 font-semibold">Ligand Atom</th>
                          <th className="px-3 py-2 font-semibold">Distance</th>
                          <th className="px-3 py-2 font-semibold">Type</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border/60">
                        {analysis.contacts.map((contact, idx) => (
                          <tr key={idx} className="hover:bg-muted/20 transition-colors">
                            <td className="px-3 py-1.5 font-bold font-mono text-primary">
                              {contact.residue_name}{contact.residue_number}:{contact.chain_id}
                            </td>
                            <td className="px-3 py-1.5 font-mono text-[11px] text-foreground">
                              {contact.atom_name}
                            </td>
                            <td className="px-3 py-1.5 font-mono text-[11px] text-emerald-600 dark:text-emerald-400">
                              {contact.ligand_atom_name}
                            </td>
                            <td className="px-3 py-1.5 font-mono text-[11px]">
                              {contact.distance_angstroms.toFixed(2)} Å
                            </td>
                            <td className="px-3 py-1.5">
                              {getContactBadge(contact.interaction_type)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Save Modal */}
            <Dialog open={saveModalOpen} onOpenChange={setSaveModalOpen}>
              <DialogContent className="sm:max-w-md">
                <DialogHeader>
                  <DialogTitle className="text-base font-bold">Save Docking Assay to Project</DialogTitle>
                  <DialogDescription className="text-xs">
                    Store affinity score and binding pocket metrics for {analysis.pdb_id} + {analysis.ligand_id}.
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
                      <span>Successfully saved docking assay to project!</span>
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
          </div>
        )}
      </div>
    </>
  );
}
