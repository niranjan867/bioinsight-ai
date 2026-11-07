"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Atom,
  Search,
  Download,
  Plus,
  Check,
  AlertCircle,
  ShieldCheck,
  ShieldAlert,
  Target,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { apiRequest, getApiBaseUrl } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

interface CompoundHit {
  cid: number;
  name: string;
  molecular_formula: string | null;
  molecular_weight: number | null;
  canonical_smiles: string | null;
  inchi_key: string | null;
  image_url: string;
}

interface CompoundSearchResponse {
  query: string;
  total: number;
  results: CompoundHit[];
}

interface Lipinski {
  molecular_weight_pass: boolean;
  logp_pass: boolean;
  h_bond_donors_pass: boolean;
  h_bond_acceptors_pass: boolean;
  violations_count: number;
  is_druglike: boolean;
}

interface DrugTarget {
  mechanism_of_action: string;
  target_name: string;
  target_chembl_id: string | null;
  action_type: string | null;
  references: string[];
}

interface CompoundDetail {
  cid: number;
  name: string;
  iupac_name: string | null;
  molecular_formula: string | null;
  molecular_weight: number | null;
  canonical_smiles: string | null;
  isomeric_smiles: string | null;
  inchi_key: string | null;
  xlogp: number | null;
  tpsa: number | null;
  h_bond_donor_count: number | null;
  h_bond_acceptor_count: number | null;
  rotatable_bond_count: number | null;
  exact_mass: number | null;
  image_url: string;
  lipinski: Lipinski;
  chembl_id: string | null;
  drug_targets: DrugTarget[];
  source: string;
  is_cached: boolean;
  retrieved_at: string;
}

interface ProjectSummary {
  id: number;
  name: string;
}

export default function CompoundsPage() {
  const { user } = useAuth();
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [searchResults, setSearchResults] = useState<CompoundHit[]>([]);
  const [selectedCompound, setSelectedCompound] = useState<CompoundDetail | null>(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);

  // Save to project modal
  const [saveModalOpen, setSaveModalOpen] = useState(false);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [isSavingToProject, setIsSavingToProject] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const handleSearch = async (searchTerm: string) => {
    if (!searchTerm.trim()) return;
    setIsSearching(true);
    setSearchError(null);
    setSelectedCompound(null);

    try {
      const data = await apiRequest<CompoundSearchResponse>("/api/v1/compounds/search", {
        params: { q: searchTerm.trim(), limit: 15 },
      });
      setSearchResults(data.results);
      if (data.results.length === 0) {
        setSearchError(`No chemical compounds found matching "${searchTerm}".`);
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setSearchError(err.message);
      } else {
        setSearchError("PubChem query failed. Please verify connection.");
      }
    } finally {
      setIsSearching(false);
    }
  };

  const handleSelectCompound = async (hit: CompoundHit) => {
    setIsLoadingDetail(true);
    try {
      const detail = await apiRequest<CompoundDetail>(`/api/v1/compounds/${hit.cid}`);
      setSelectedCompound(detail);
    } catch (err: unknown) {
      if (err instanceof Error) {
        alert(err.message);
      }
    } finally {
      setIsLoadingDetail(false);
    }
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
      if (projs.length > 0) {
        setSelectedProjectId(projs[0].id);
      }
    } catch {
      setProjects([]);
    }
  };

  const handleSaveToProject = async () => {
    if (!selectedProjectId || !selectedCompound) return;
    setIsSavingToProject(true);
    try {
      await apiRequest(`/api/v1/projects/${selectedProjectId}/items`, {
        method: "POST",
        body: {
          item_type: "compound",
          item_id: `CID:${selectedCompound.cid}`,
          title: selectedCompound.name,
          description: `${selectedCompound.molecular_formula || "Small Molecule"} (MW: ${selectedCompound.molecular_weight || "N/A"})`,
          metadata_json: {
            smiles: selectedCompound.canonical_smiles,
            inchi_key: selectedCompound.inchi_key,
            chembl_id: selectedCompound.chembl_id,
            druglike: selectedCompound.lipinski.is_druglike,
          },
        },
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveModalOpen(false), 1200);
    } catch (err: unknown) {
      if (err instanceof Error) {
        alert(err.message);
      }
    } finally {
      setIsSavingToProject(false);
    }
  };

  const handleDownloadSdf = () => {
    if (!selectedCompound) return;
    const url = `${getApiBaseUrl()}/api/v1/compounds/${selectedCompound.cid}/sdf`;
    window.open(url, "_blank");
  };

  return (
    <div className="space-y-6 p-6 md:p-8">
      {/* Title & Overview */}
      <div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="border-emerald-500/30 text-emerald-500 text-[10px]">
            <Atom className="mr-1 h-3 w-3" />
            Cheminformatics
          </Badge>
          <span className="text-xs text-muted-foreground">PubChem PUG REST & ChEMBL</span>
        </div>
        <h1 className="mt-1 text-2xl font-bold tracking-tight text-foreground">
          Compound Intelligence
        </h1>
        <p className="text-xs text-muted-foreground">
          Search small molecules, inspect chemical structures, evaluate Lipinski Rule of 5, and analyze drug-target relationships
        </p>
      </div>

      {/* Search Input & Quick Queries */}
      <Card className="border-border/80 bg-card shadow-xs">
        <CardContent className="pt-5 space-y-3">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSearch(query);
            }}
            className="flex gap-2"
          >
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Search compound by name or SMILES (e.g. Aspirin, Metformin, Ibuprofen, Paclitaxel)..."
                className="pl-9 text-xs"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>
            <Button type="submit" size="sm" className="h-9 text-xs font-semibold gap-1.5" disabled={isSearching || !query.trim()}>
              <Search className="h-3.5 w-3.5" />
              <span>{isSearching ? "Searching..." : "Search"}</span>
            </Button>
          </form>

          <div className="flex flex-wrap items-center gap-1.5 text-xs">
            <span className="text-[11px] text-muted-foreground">Quick queries:</span>
            {["Aspirin", "Metformin", "Ibuprofen", "Paclitaxel", "Atorvastatin", "Doxorubicin"].map((term) => (
              <button
                key={term}
                type="button"
                onClick={() => {
                  setQuery(term);
                  handleSearch(term);
                }}
                className="rounded-md border border-border bg-muted/40 px-2 py-0.5 text-[11px] text-foreground hover:bg-muted transition-colors"
              >
                {term}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left Column: Search Results */}
        <div className="space-y-3 lg:col-span-1">
          <h2 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
            Compounds ({searchResults.length})
          </h2>

          {isSearching ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-20 animate-pulse rounded-lg bg-card border border-border/60" />
              ))}
            </div>
          ) : searchError ? (
            <div className="flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{searchError}</span>
            </div>
          ) : searchResults.length === 0 ? (
            <div className="rounded-lg border border-dashed border-border/80 p-8 text-center text-xs text-muted-foreground">
              Search a bioactive compound to explore its molecular properties
            </div>
          ) : (
            <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
              {searchResults.map((hit) => {
                const isSelected = selectedCompound?.cid === hit.cid;
                return (
                  <button
                    key={hit.cid}
                    type="button"
                    onClick={() => handleSelectCompound(hit)}
                    className={`w-full text-left rounded-lg border p-3 text-xs transition-all flex items-center gap-3 ${
                      isSelected
                        ? "border-primary bg-primary/5 shadow-xs"
                        : "border-border/80 bg-card hover:border-primary/40"
                    }`}
                  >
                    {/* Chemical Structure Thumbnail */}
                    <div className="h-12 w-12 shrink-0 rounded bg-white p-1 border border-border/60 flex items-center justify-center overflow-hidden">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={hit.image_url}
                        alt={hit.name}
                        className="max-h-full max-w-full object-contain"
                        loading="lazy"
                      />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-1">
                        <span className="font-semibold text-foreground line-clamp-1">{hit.name}</span>
                        <span className="font-mono text-[10px] text-muted-foreground shrink-0">CID:{hit.cid}</span>
                      </div>
                      <div className="flex items-center gap-2 text-[10px] text-muted-foreground mt-0.5">
                        {hit.molecular_formula && <span>{hit.molecular_formula}</span>}
                        {hit.molecular_weight && <span>• {hit.molecular_weight} Da</span>}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column: Detailed Compound Inspector */}
        <div className="lg:col-span-2">
          {isLoadingDetail ? (
            <Card className="h-96 animate-pulse border-border/60 bg-card" />
          ) : selectedCompound ? (
            <Card className="border-border/80 bg-card shadow-xs">
              <CardHeader className="pb-3 border-b border-border/60">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-[10px] font-mono">
                        PubChem CID {selectedCompound.cid}
                      </Badge>
                      {selectedCompound.chembl_id && (
                        <Badge variant="secondary" className="text-[10px] font-mono">
                          {selectedCompound.chembl_id}
                        </Badge>
                      )}
                      {selectedCompound.is_cached && (
                        <Badge variant="outline" className="text-[10px] text-emerald-600 border-emerald-500/30">
                          Cached
                        </Badge>
                      )}
                    </div>
                    <CardTitle className="mt-1 text-lg font-bold text-foreground">
                      {selectedCompound.name}
                    </CardTitle>
                    <CardDescription className="text-xs">
                      {selectedCompound.iupac_name || selectedCompound.canonical_smiles}
                    </CardDescription>
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={handleDownloadSdf}
                      className="h-8 text-xs gap-1.5"
                    >
                      <Download className="h-3.5 w-3.5" />
                      <span>3D SDF</span>
                    </Button>

                    {/* Save to Project Dialog */}
                    <Button size="sm" onClick={openSaveDialog} className="h-8 text-xs gap-1.5 font-semibold">
                      <Plus className="h-3.5 w-3.5" />
                      <span>Save</span>
                    </Button>

                    <Dialog open={saveModalOpen} onOpenChange={setSaveModalOpen}>
                      <DialogContent className="sm:max-w-md">
                        <DialogHeader>
                          <DialogTitle className="text-base font-bold">Save Compound to Project</DialogTitle>
                          <DialogDescription className="text-xs">
                            Add {selectedCompound.name} (CID: {selectedCompound.cid}) to a research workspace.
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
                              <span>Successfully saved compound to project!</span>
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
                </div>
              </CardHeader>

              <CardContent className="pt-4 space-y-5">
                {/* 2D Structure + Lipinski Summary Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 items-center">
                  {/* Structure Image */}
                  <div className="rounded-xl border border-border/80 bg-white p-3 flex items-center justify-center h-44 shadow-xs">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={selectedCompound.image_url}
                      alt={selectedCompound.name}
                      className="max-h-full max-w-full object-contain"
                    />
                  </div>

                  {/* Lipinski Rule of 5 Card */}
                  <div className="sm:col-span-2 rounded-xl border border-border/80 bg-muted/20 p-4 space-y-2.5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                        Lipinski&apos;s Rule of 5
                      </span>
                      {selectedCompound.lipinski.is_druglike ? (
                        <Badge className="bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 text-[10px] gap-1">
                          <ShieldCheck className="h-3 w-3" />
                          <span>Drug-like ({selectedCompound.lipinski.violations_count} violations)</span>
                        </Badge>
                      ) : (
                        <Badge variant="destructive" className="text-[10px] gap-1">
                          <ShieldAlert className="h-3 w-3" />
                          <span>{selectedCompound.lipinski.violations_count} Violations</span>
                        </Badge>
                      )}
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="rounded bg-background p-2 border border-border/60">
                        <span className="text-[10px] text-muted-foreground block">Mol. Weight</span>
                        <span className="font-semibold">{selectedCompound.molecular_weight || "N/A"} Da</span>
                        <span className="text-[9px] text-muted-foreground block">Cutoff: ≤ 500 Da</span>
                      </div>
                      <div className="rounded bg-background p-2 border border-border/60">
                        <span className="text-[10px] text-muted-foreground block">Partition Coeff (LogP)</span>
                        <span className="font-semibold">{selectedCompound.xlogp ?? "N/A"}</span>
                        <span className="text-[9px] text-muted-foreground block">Cutoff: ≤ 5.0</span>
                      </div>
                      <div className="rounded bg-background p-2 border border-border/60">
                        <span className="text-[10px] text-muted-foreground block">H-Bond Donors</span>
                        <span className="font-semibold">{selectedCompound.h_bond_donor_count ?? 0}</span>
                        <span className="text-[9px] text-muted-foreground block">Cutoff: ≤ 5</span>
                      </div>
                      <div className="rounded bg-background p-2 border border-border/60">
                        <span className="text-[10px] text-muted-foreground block">H-Bond Acceptors</span>
                        <span className="font-semibold">{selectedCompound.h_bond_acceptor_count ?? 0}</span>
                        <span className="text-[9px] text-muted-foreground block">Cutoff: ≤ 10</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Additional Molecular Properties */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                  <div className="rounded-lg border border-border/60 bg-muted/10 p-2.5">
                    <span className="text-[10px] text-muted-foreground block">Formula</span>
                    <span className="font-mono font-semibold">{selectedCompound.molecular_formula || "N/A"}</span>
                  </div>
                  <div className="rounded-lg border border-border/60 bg-muted/10 p-2.5">
                    <span className="text-[10px] text-muted-foreground block">Polar Surface Area</span>
                    <span className="font-semibold">{selectedCompound.tpsa ?? "N/A"} Å²</span>
                  </div>
                  <div className="rounded-lg border border-border/60 bg-muted/10 p-2.5">
                    <span className="text-[10px] text-muted-foreground block">Rotatable Bonds</span>
                    <span className="font-semibold">{selectedCompound.rotatable_bond_count ?? "N/A"}</span>
                  </div>
                  <div className="rounded-lg border border-border/60 bg-muted/10 p-2.5">
                    <span className="text-[10px] text-muted-foreground block">Exact Mass</span>
                    <span className="font-semibold">{selectedCompound.exact_mass ?? "N/A"}</span>
                  </div>
                </div>

                {/* SMILES & InChIKey */}
                <div className="space-y-1.5 text-xs">
                  <div className="rounded-lg bg-muted/20 p-2.5 border border-border/60">
                    <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider block">
                      Canonical SMILES
                    </span>
                    <span className="font-mono text-[11px] text-primary break-all select-all">
                      {selectedCompound.canonical_smiles || "N/A"}
                    </span>
                  </div>
                  <div className="rounded-lg bg-muted/20 p-2.5 border border-border/60">
                    <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider block">
                      InChIKey
                    </span>
                    <span className="font-mono text-[11px] text-foreground break-all select-all">
                      {selectedCompound.inchi_key || "N/A"}
                    </span>
                  </div>
                </div>

                {/* ChEMBL Drug Target Relationships */}
                <div className="space-y-2">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                    <Target className="h-3.5 w-3.5 text-primary" />
                    <span>Biological Targets & Pharmacological Action ({selectedCompound.drug_targets.length})</span>
                  </h3>

                  {selectedCompound.drug_targets.length === 0 ? (
                    <div className="rounded-lg border border-dashed border-border/60 p-4 text-center text-xs text-muted-foreground">
                      No curated ChEMBL drug-target mechanisms recorded for this compound.
                    </div>
                  ) : (
                    <div className="overflow-x-auto rounded-lg border border-border/60">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-muted/50 text-[10px] uppercase tracking-wider text-muted-foreground border-b border-border/60">
                          <tr>
                            <th className="px-3 py-2 font-semibold">Biological Target</th>
                            <th className="px-3 py-2 font-semibold">Mechanism of Action</th>
                            <th className="px-3 py-2 font-semibold">Action Type</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-border/60">
                          {selectedCompound.drug_targets.map((tgt, idx) => (
                            <tr key={idx} className="hover:bg-muted/20 transition-colors">
                              <td className="px-3 py-2 font-semibold text-foreground">
                                {tgt.target_name}
                                {tgt.target_chembl_id && (
                                  <span className="block font-mono text-[9px] text-muted-foreground">
                                    {tgt.target_chembl_id}
                                  </span>
                                )}
                              </td>
                              <td className="px-3 py-2 text-muted-foreground">
                                {tgt.mechanism_of_action}
                              </td>
                              <td className="px-3 py-2">
                                <Badge variant="outline" className="text-[10px] capitalize">
                                  {tgt.action_type || "Modulator"}
                                </Badge>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="flex h-72 items-center justify-center rounded-xl border border-dashed border-border/80 bg-muted/20 p-8 text-center">
              <div>
                <Atom className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                <p className="text-xs font-semibold text-foreground">Select a Chemical Compound</p>
                <p className="text-[11px] text-muted-foreground mt-1 max-w-sm mx-auto">
                  Pick a small molecule from search results to view 2D chemical structure, Lipinski drug-likeness rules, and ChEMBL pharmacological targets.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
