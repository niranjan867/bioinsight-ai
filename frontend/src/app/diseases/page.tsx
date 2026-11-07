"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  HeartPulse,
  Search,
  BookOpen,
  Dna,
  ExternalLink,
  Plus,
  Check,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { apiRequest } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

interface DiseaseHit {
  id: string;
  name: string;
  description: string | null;
  entity: string;
}

interface DiseaseSearchResponse {
  query: string;
  total: number;
  results: DiseaseHit[];
}

interface AssociatedTarget {
  target_id: string;
  symbol: string;
  name: string;
  score: number;
}

interface DiseaseDetail {
  id: string;
  name: string;
  description: string | null;
  therapeutic_areas: { id: string; name: string }[];
  synonyms: string[];
  source: string;
  associated_targets: AssociatedTarget[];
  is_cached: boolean;
  retrieved_at: string;
}

interface PublicationHit {
  id: string;
  title: string;
  authors: string | null;
  journal: string | null;
  pub_year: number | null;
  pmid: string | null;
  doi: string | null;
  cited_by_count: number | null;
}

interface PublicationsResponse {
  disease_id: string;
  disease_name: string;
  total: number;
  publications: PublicationHit[];
}

interface ProjectSummary {
  id: number;
  name: string;
}

export default function DiseasesPage() {
  const { user } = useAuth();
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [searchResults, setSearchResults] = useState<DiseaseHit[]>([]);
  const [selectedDisease, setSelectedDisease] = useState<DiseaseDetail | null>(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [publications, setPublications] = useState<PublicationHit[]>([]);
  const [isLoadingPubs, setIsLoadingPubs] = useState(false);

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
    setSelectedDisease(null);

    try {
      const data = await apiRequest<DiseaseSearchResponse>("/api/v1/diseases/search", {
        params: { q: searchTerm.trim(), size: 20 },
      });
      setSearchResults(data.results);
      if (data.results.length === 0) {
        setSearchError(`No diseases found matching "${searchTerm}".`);
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setSearchError(err.message);
      } else {
        setSearchError("Disease query failed. Please verify network access.");
      }
    } finally {
      setIsSearching(false);
    }
  };

  const handleSelectDisease = async (hit: DiseaseHit) => {
    setIsLoadingDetail(true);
    setIsLoadingPubs(true);
    try {
      const detail = await apiRequest<DiseaseDetail>(`/api/v1/diseases/${hit.id}`);
      setSelectedDisease(detail);

      // Load publications from Europe PMC
      const pubs = await apiRequest<PublicationsResponse>(`/api/v1/diseases/${hit.id}/publications`, {
        params: { name: detail.name, size: 10 },
      });
      setPublications(pubs.publications);
    } catch (err: unknown) {
      if (err instanceof Error) {
        alert(err.message);
      }
    } finally {
      setIsLoadingDetail(false);
      setIsLoadingPubs(false);
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
    if (!selectedProjectId || !selectedDisease) return;
    setIsSavingToProject(true);
    try {
      await apiRequest(`/api/v1/projects/${selectedProjectId}/items`, {
        method: "POST",
        body: {
          item_type: "disease",
          item_id: selectedDisease.id,
          title: selectedDisease.name,
          description: selectedDisease.description || undefined,
          metadata_json: {
            therapeutic_areas: selectedDisease.therapeutic_areas,
            targets_count: selectedDisease.associated_targets.length,
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

  return (
    <div className="space-y-6 p-6 md:p-8">
      {/* Title & Overview */}
      <div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="border-rose-500/30 text-rose-500 text-[10px]">
            <HeartPulse className="mr-1 h-3 w-3" />
            Clinical Genetics
          </Badge>
          <span className="text-xs text-muted-foreground">Open Targets & Europe PMC</span>
        </div>
        <h1 className="mt-1 text-2xl font-bold tracking-tight text-foreground">
          Disease Intelligence
        </h1>
        <p className="text-xs text-muted-foreground">
          Investigate disease phenotypes, therapeutic areas, associated genetic targets, and scientific literature
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
                placeholder="Search disease by name (e.g. Asthma, Breast Cancer, Alzheimer, Diabetes)..."
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
            {["Asthma", "Breast Cancer", "Alzheimer's Disease", "Type 2 Diabetes", "Melanoma"].map((term) => (
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
            Diseases ({searchResults.length})
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
              Search a disease to view matching clinical entries
            </div>
          ) : (
            <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
              {searchResults.map((hit) => {
                const isSelected = selectedDisease?.id === hit.id;
                return (
                  <button
                    key={hit.id}
                    type="button"
                    onClick={() => handleSelectDisease(hit)}
                    className={`w-full text-left rounded-lg border p-3 text-xs transition-all ${
                      isSelected
                        ? "border-primary bg-primary/5 shadow-xs"
                        : "border-border/80 bg-card hover:border-primary/40"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-1">
                      <span className="font-semibold text-foreground line-clamp-1">{hit.name}</span>
                      <span className="font-mono text-[10px] text-muted-foreground shrink-0">{hit.id}</span>
                    </div>
                    {hit.description && (
                      <p className="mt-1 line-clamp-2 text-[11px] text-muted-foreground leading-relaxed">
                        {hit.description}
                      </p>
                    )}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column: Detailed Disease Inspector */}
        <div className="lg:col-span-2">
          {isLoadingDetail ? (
            <Card className="h-96 animate-pulse border-border/60 bg-card" />
          ) : selectedDisease ? (
            <Card className="border-border/80 bg-card shadow-xs">
              <CardHeader className="pb-3 border-b border-border/60">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-[10px] font-mono uppercase">
                        {selectedDisease.id}
                      </Badge>
                      {selectedDisease.is_cached && (
                        <Badge variant="secondary" className="text-[10px]">
                          Cached in PostgreSQL
                        </Badge>
                      )}
                    </div>
                    <CardTitle className="mt-1 text-lg font-bold text-foreground">
                      {selectedDisease.name}
                    </CardTitle>
                    <CardDescription className="text-xs">
                      Primary source: Open Targets Platform API v4
                    </CardDescription>
                  </div>

                  {/* Save to Project Button */}
                  <Button size="sm" onClick={openSaveDialog} className="h-8 text-xs gap-1.5 font-semibold">
                    <Plus className="h-3.5 w-3.5" />
                    <span>Save to Project</span>
                  </Button>

                  <Dialog open={saveModalOpen} onOpenChange={setSaveModalOpen}>
                    <DialogContent className="sm:max-w-md">
                      <DialogHeader>
                        <DialogTitle className="text-base font-bold">Save Disease to Project</DialogTitle>
                        <DialogDescription className="text-xs">
                          Add {selectedDisease.name} ({selectedDisease.id}) to an active research workspace.
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
                            <span>Successfully saved to project!</span>
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

                {/* Therapeutic Areas */}
                {selectedDisease.therapeutic_areas.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {selectedDisease.therapeutic_areas.map((ta) => (
                      <Badge key={ta.id} variant="secondary" className="text-[10px] font-medium">
                        {ta.name}
                      </Badge>
                    ))}
                  </div>
                )}
              </CardHeader>

              <CardContent className="pt-4 space-y-4">
                {selectedDisease.description && (
                  <div className="rounded-lg bg-muted/30 p-3 text-xs leading-relaxed text-muted-foreground border border-border/60">
                    <span className="font-semibold text-foreground">Clinical Summary: </span>
                    {selectedDisease.description}
                  </div>
                )}

                <Tabs defaultValue="targets" className="space-y-3">
                  <TabsList className="bg-muted/60 p-1">
                    <TabsTrigger value="targets" className="text-xs gap-1.5">
                      <Dna className="h-3.5 w-3.5 text-blue-500" />
                      <span>Associated Targets ({selectedDisease.associated_targets.length})</span>
                    </TabsTrigger>
                    <TabsTrigger value="publications" className="text-xs gap-1.5">
                      <BookOpen className="h-3.5 w-3.5 text-emerald-500" />
                      <span>Publications ({publications.length})</span>
                    </TabsTrigger>
                  </TabsList>

                  {/* Associated Targets Tab */}
                  <TabsContent value="targets" className="space-y-2">
                    {selectedDisease.associated_targets.length === 0 ? (
                      <p className="text-xs text-muted-foreground p-4 text-center">No associated genetic targets returned.</p>
                    ) : (
                      <div className="overflow-x-auto rounded-lg border border-border/60">
                        <table className="w-full text-left text-xs">
                          <thead className="bg-muted/50 text-[11px] uppercase tracking-wider text-muted-foreground border-b border-border/60">
                            <tr>
                              <th className="px-3 py-2 font-semibold">Target Symbol</th>
                              <th className="px-3 py-2 font-semibold">Full Name</th>
                              <th className="px-3 py-2 font-semibold">Association Score</th>
                              <th className="px-3 py-2 text-right">Action</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-border/60">
                            {selectedDisease.associated_targets.map((target) => (
                              <tr key={target.target_id} className="hover:bg-muted/20 transition-colors">
                                <td className="px-3 py-2 font-bold text-primary font-mono">
                                  {target.symbol}
                                </td>
                                <td className="px-3 py-2 text-muted-foreground truncate max-w-[200px]">
                                  {target.name}
                                </td>
                                <td className="px-3 py-2">
                                  <div className="flex items-center gap-2">
                                    <div className="h-1.5 w-16 bg-muted rounded-full overflow-hidden">
                                      <div
                                        className="h-full bg-primary rounded-full"
                                        style={{ width: `${Math.round(target.score * 100)}%` }}
                                      />
                                    </div>
                                    <span className="font-mono text-[11px] text-foreground font-semibold">
                                      {target.score.toFixed(3)}
                                    </span>
                                  </div>
                                </td>
                                <td className="px-3 py-2 text-right">
                                  <Link href={`/genes`}>
                                    <Button variant="ghost" size="sm" className="h-6 text-[11px] gap-1 text-primary">
                                      <span>Inspect Gene</span>
                                      <ExternalLink className="h-2.5 w-2.5" />
                                    </Button>
                                  </Link>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </TabsContent>

                  {/* Publications Tab */}
                  <TabsContent value="publications" className="space-y-3">
                    {isLoadingPubs ? (
                      <p className="text-xs text-muted-foreground p-4 text-center animate-pulse">Loading literature from Europe PMC...</p>
                    ) : publications.length === 0 ? (
                      <p className="text-xs text-muted-foreground p-4 text-center">No recent publications found on Europe PMC.</p>
                    ) : (
                      <div className="space-y-2.5 max-h-[450px] overflow-y-auto pr-1">
                        {publications.map((pub) => (
                          <div key={pub.id} className="rounded-lg border border-border/60 bg-muted/10 p-3 space-y-1">
                            <h4 className="text-xs font-semibold text-foreground line-clamp-2">
                              {pub.title}
                            </h4>
                            <div className="flex flex-wrap items-center gap-2 text-[10px] text-muted-foreground">
                              {pub.journal && <span className="font-medium text-foreground">{pub.journal}</span>}
                              {pub.pub_year && <span>({pub.pub_year})</span>}
                              {pub.authors && <span className="truncate max-w-[220px]">By {pub.authors}</span>}
                              {pub.pmid && (
                                <a
                                  href={`https://pubmed.ncbi.nlm.nih.gov/${pub.pmid}/`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-primary hover:underline flex items-center gap-0.5"
                                >
                                  PMID:{pub.pmid}
                                  <ExternalLink className="h-2.5 w-2.5" />
                                </a>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          ) : (
            <div className="flex h-72 items-center justify-center rounded-xl border border-dashed border-border/80 bg-muted/20 p-8 text-center">
              <div>
                <HeartPulse className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                <p className="text-xs font-semibold text-foreground">Select a Disease Record</p>
                <p className="text-[11px] text-muted-foreground mt-1 max-w-sm mx-auto">
                  Choose a disease from search results to inspect genetic associations from Open Targets and scientific papers from Europe PMC.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
