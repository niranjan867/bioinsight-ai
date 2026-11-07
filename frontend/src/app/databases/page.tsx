"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Database,
  Search,
  ExternalLink,
  Layers,
  Activity,
  Atom,
  Dna,
  FileText,
  Share2,
  Crosshair,
  HeartPulse,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Sparkles,
  ArrowRight,
  Filter,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { apiRequest } from "@/lib/api";

interface ConnectorMetadata {
  id: string;
  name: string;
  description: string;
  category: string;
  home_url: string;
  api_docs_url: string;
  icon: string;
  is_active: boolean;
  rate_limit_per_minute: number;
}

interface NormalizedRecord {
  id: string;
  source_database: string;
  database_name: string;
  category: string;
  title: string;
  scientific_name?: string | null;
  description?: string | null;
  external_url: string;
  metadata: Record<string, unknown>;
}

interface DatabaseStatus {
  database_id: string;
  database_name: string;
  status: string;
  hits?: number;
  total_hits?: number;
  execution_time_ms?: number;
  error?: string | null;
}

interface GlobalSearchResponse {
  query: string;
  total_results: number;
  execution_time_ms: number;
  categories_found: string[];
  results_by_category: Record<string, NormalizedRecord[]>;
  database_statuses: DatabaseStatus[];
}

const CATEGORY_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  structures: Layers,
  proteins: Activity,
  compounds: Atom,
  genes: Dna,
  publications: FileText,
  pathways: Share2,
  targets: Crosshair,
  diseases: HeartPulse,
};

const CATEGORY_COLORS: Record<string, string> = {
  structures: "bg-blue-500/10 text-blue-600 border-blue-500/20",
  proteins: "bg-emerald-500/10 text-emerald-600 border-emerald-500/20",
  compounds: "bg-amber-500/10 text-amber-600 border-amber-500/20",
  genes: "bg-purple-500/10 text-purple-600 border-purple-500/20",
  publications: "bg-slate-500/10 text-slate-600 border-slate-500/20",
  pathways: "bg-cyan-500/10 text-cyan-600 border-cyan-500/20",
  targets: "bg-rose-500/10 text-rose-600 border-rose-500/20",
  diseases: "bg-red-500/10 text-red-600 border-red-500/20",
};

const SUGGESTED_QUERIES = [
  "BRCA1",
  "TP53",
  "EGFR",
  "Aspirin",
  "Imatinib",
  "4HHB",
  "Glioblastoma",
];

export default function ScientificDatabaseHubPage() {
  const [connectors, setConnectors] = useState<ConnectorMetadata[]>([]);
  const [searchQuery, setSearchQuery] = useState("BRCA1");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [isSearching, setIsSearching] = useState(false);
  const [searchResponse, setSearchResponse] = useState<GlobalSearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Detail Modal
  const [selectedRecord, setSelectedRecord] = useState<NormalizedRecord | null>(null);
  const [detailModalOpen, setDetailModalOpen] = useState(false);

  // Search History
  const [searchHistory, setSearchHistory] = useState<string[]>(["BRCA1", "TP53", "Aspirin"]);

  const performSearch = async (queryToSearch: string) => {
    if (!queryToSearch.trim()) return;
    setIsSearching(true);
    setError(null);

    try {
      const payload: { query: string; limit: number; categories?: string[] } = {
        query: queryToSearch.trim(),
        limit: 10,
      };

      if (selectedCategory !== "all") {
        payload.categories = [selectedCategory];
      }

      const res = await apiRequest<GlobalSearchResponse>("/api/v1/databases/search", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      setSearchResponse(res);

      setSearchHistory((prev) => {
        const next = [queryToSearch.trim(), ...prev.filter((q) => q.toLowerCase() !== queryToSearch.trim().toLowerCase())];
        return next.slice(0, 8);
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Search request failed";
      setError(msg);
    } finally {
      setIsSearching(false);
    }
  };

  useEffect(() => {
    let ignore = false;
    async function loadInitial() {
      try {
        const [connData, searchData] = await Promise.all([
          apiRequest<ConnectorMetadata[]>("/api/v1/databases/connectors"),
          apiRequest<GlobalSearchResponse>("/api/v1/databases/search", {
            method: "POST",
            body: JSON.stringify({ query: "BRCA1", limit: 10 }),
          }),
        ]);
        if (!ignore) {
          setConnectors(connData);
          setSearchResponse(searchData);
        }
      } catch (err) {
        console.error("Initial load error", err);
      }
    }
    loadInitial();
    return () => {
      ignore = true;
    };
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    performSearch(searchQuery);
  };

  // Filter results by selected category tab
  const displayedCategories = searchResponse?.categories_found.filter(
    (cat) => selectedCategory === "all" || selectedCategory === cat
  ) || [];

  return (
    <div className="container mx-auto space-y-8 p-4 md:p-6 max-w-7xl">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary/10 via-background to-accent/15 p-6 md:p-8 border shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
              <Database className="h-3.5 w-3.5" />
              11 Authoritative Biological Databases
            </div>
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight">
              Scientific Database Hub & Global Search
            </h1>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Federated, parallel discovery across the world&apos;s primary biological repositories:
              RCSB PDB, UniProtKB, PubChem, NCBI Entrez, PDBe, AlphaFold DB, ChEMBL, Europe PMC,
              Open Targets, Ensembl, and Reactome.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-3">
            <Link
              href="/docking"
              className="inline-flex items-center gap-2 rounded-md border border-input bg-background px-4 py-2 text-xs font-medium shadow-xs hover:bg-accent hover:text-accent-foreground"
            >
              <Crosshair className="h-4 w-4" />
              Docking Workbench
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>

        {/* Global Search Input */}
        <form onSubmit={handleSearchSubmit} className="mt-6 flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search across all 11 scientific databases (e.g. gene, protein, PDB ID, compound, SMILES, target)..."
              className="pl-10 h-11 bg-background text-sm shadow-xs"
            />
          </div>
          <Button type="submit" disabled={isSearching} className="h-11 px-6 gap-2">
            {isSearching ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
            Global Search
          </Button>
        </form>

        {/* Quick query tags */}
        <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          <span className="font-medium flex items-center gap-1">
            <Sparkles className="h-3 w-3 text-primary" /> Suggestions:
          </span>
          {SUGGESTED_QUERIES.map((q) => (
            <button
              key={q}
              type="button"
              onClick={() => {
                setSearchQuery(q);
                performSearch(q);
              }}
              className="rounded-md bg-muted px-2 py-0.5 font-medium hover:bg-primary/20 hover:text-primary transition-colors cursor-pointer"
            >
              {q}
            </button>
          ))}

          {searchHistory.length > 0 && (
            <>
              <span className="ml-2 font-medium text-muted-foreground">• Recent:</span>
              {searchHistory.slice(0, 4).map((hist) => (
                <button
                  key={`hist-${hist}`}
                  type="button"
                  onClick={() => {
                    setSearchQuery(hist);
                    performSearch(hist);
                  }}
                  className="rounded-md border border-muted-foreground/20 bg-background/50 px-2 py-0.5 font-medium hover:border-primary/40 transition-colors cursor-pointer"
                >
                  {hist}
                </button>
              ))}
            </>
          )}
        </div>
      </div>

      {/* Connected Databases Status Strip */}
      <Card>
        <CardHeader className="py-3 px-4 border-b">
          <div className="flex items-center justify-between">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              Active Scientific Data Connectors ({connectors.length})
            </CardTitle>
            <span className="text-[11px] text-muted-foreground">
              Official REST & GraphQL APIs
            </span>
          </div>
        </CardHeader>
        <CardContent className="p-3">
          <div className="flex flex-wrap gap-2">
            {connectors.map((c) => (
              <a
                key={c.id}
                href={c.home_url}
                target="_blank"
                rel="noreferrer"
                className="group flex items-center gap-1.5 rounded-lg border bg-card px-2.5 py-1 text-xs font-medium text-foreground hover:border-primary/50 transition-colors"
                title={`${c.name}: ${c.description}`}
              >
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                <span>{c.name}</span>
                <ExternalLink className="h-3 w-3 text-muted-foreground group-hover:text-primary transition-colors" />
              </a>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Category Filter Pills & Metrics */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-1.5">
          <Button
            size="sm"
            variant={selectedCategory === "all" ? "default" : "outline"}
            onClick={() => setSelectedCategory("all")}
            className="h-8 text-xs font-medium"
          >
            All Categories
          </Button>
          {["genes", "proteins", "structures", "compounds", "targets", "publications", "pathways", "diseases"].map((cat) => {
            const Icon = CATEGORY_ICONS[cat] || Filter;
            const count = searchResponse?.results_by_category[cat]?.length || 0;
            return (
              <Button
                key={cat}
                size="sm"
                variant={selectedCategory === cat ? "default" : "outline"}
                onClick={() => setSelectedCategory(cat)}
                className="h-8 text-xs font-medium capitalize gap-1.5"
              >
                <Icon className="h-3.5 w-3.5" />
                {cat}
                {count > 0 && (
                  <Badge variant="secondary" className="ml-1 text-[10px] px-1 py-0 h-4">
                    {count}
                  </Badge>
                )}
              </Button>
            );
          })}
        </div>

        {searchResponse && (
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <Clock className="h-3.5 w-3.5" />
              {searchResponse.execution_time_ms} ms
            </span>
            <span>•</span>
            <span className="font-semibold text-foreground">
              {searchResponse.total_results} matching records
            </span>
          </div>
        )}
      </div>

      {/* Error Banner */}
      {error && (
        <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive flex items-center gap-3">
          <AlertTriangle className="h-5 w-5 shrink-0" />
          <div>
            <div className="font-semibold">Search Execution Notice</div>
            <div>{error}</div>
          </div>
        </div>
      )}

      {/* Database Search Results Grid */}
      {isSearching ? (
        <div className="flex flex-col items-center justify-center py-20 space-y-3">
          <RefreshCw className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Querying 11 scientific databases concurrently...</p>
        </div>
      ) : searchResponse && displayedCategories.length > 0 ? (
        <div className="space-y-8">
          {displayedCategories.map((category) => {
            const records = searchResponse.results_by_category[category] || [];
            const Icon = CATEGORY_ICONS[category] || Database;
            const colorClass = CATEGORY_COLORS[category] || "bg-muted text-foreground";

            return (
              <div key={category} className="space-y-3">
                <div className="flex items-center gap-2 border-b pb-2">
                  <div className={`p-1.5 rounded-lg border ${colorClass}`}>
                    <Icon className="h-4 w-4" />
                  </div>
                  <h2 className="text-lg font-bold capitalize tracking-tight">
                    {category} ({records.length})
                  </h2>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {records.map((rec) => (
                    <Card key={`${rec.source_database}-${rec.id}`} className="flex flex-col justify-between hover:shadow-md transition-shadow">
                      <CardHeader className="pb-2">
                        <div className="flex items-start justify-between gap-2">
                          <Badge variant="outline" className={`text-[10px] font-semibold uppercase ${colorClass}`}>
                            {rec.database_name}
                          </Badge>
                          <span className="text-[11px] font-mono text-muted-foreground">
                            {rec.id}
                          </span>
                        </div>
                        <CardTitle className="text-base font-semibold leading-snug line-clamp-2 mt-1">
                          {rec.title}
                        </CardTitle>
                        {rec.scientific_name && (
                          <CardDescription className="text-xs italic line-clamp-1">
                            {rec.scientific_name}
                          </CardDescription>
                        )}
                      </CardHeader>

                      <CardContent className="space-y-3 text-xs">
                        {rec.description && (
                          <p className="text-muted-foreground line-clamp-3 leading-relaxed">
                            {rec.description}
                          </p>
                        )}

                        <div className="flex items-center justify-between gap-2 pt-2 border-t">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 text-xs px-2"
                            onClick={() => {
                              setSelectedRecord(rec);
                              setDetailModalOpen(true);
                            }}
                          >
                            Inspect Detail
                          </Button>

                          <div className="flex items-center gap-1.5">
                            {/* Action to dock if structure or compound */}
                            {(category === "structures" || category === "compounds") && (
                              <Link
                                href={`/docking?${category === "structures" ? "protein=" + rec.id : "ligand=" + rec.title.split(" ")[0]}`}
                                className="inline-flex items-center gap-1 rounded-md bg-secondary px-2 py-1 text-[11px] font-medium text-primary hover:bg-secondary/80 h-7"
                              >
                                <Crosshair className="h-3 w-3" />
                                Dock
                              </Link>
                            )}

                            <a
                              href={rec.external_url}
                              target="_blank"
                              rel="noreferrer"
                              className="inline-flex items-center gap-1 rounded-md border border-input px-2 py-1 text-xs hover:bg-muted h-7"
                            >
                              <span>Source</span>
                              <ExternalLink className="h-3 w-3" />
                            </a>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      ) : searchResponse && displayedCategories.length === 0 ? (
        <div className="text-center py-16 space-y-3 border rounded-xl bg-card">
          <Database className="mx-auto h-10 w-10 text-muted-foreground/40" />
          <h3 className="text-base font-medium">No results found for &ldquo;{searchQuery}&rdquo;</h3>
          <p className="text-sm text-muted-foreground max-w-md mx-auto">
            Try searching for a standard gene symbol (BRCA1, TP53), protein accession (P04637), PDB code (4HHB), or chemical compound name.
          </p>
        </div>
      ) : null}

      {/* Record Detail Modal */}
      <Dialog open={detailModalOpen} onOpenChange={setDetailModalOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          {selectedRecord && (
            <>
              <DialogHeader>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="capitalize text-xs font-semibold">
                    {selectedRecord.category}
                  </Badge>
                  <span className="text-xs text-muted-foreground font-mono">
                    {selectedRecord.database_name} • {selectedRecord.id}
                  </span>
                </div>
                <DialogTitle className="text-lg font-bold mt-1">
                  {selectedRecord.title}
                </DialogTitle>
                {selectedRecord.scientific_name && (
                  <DialogDescription className="italic text-xs">
                    {selectedRecord.scientific_name}
                  </DialogDescription>
                )}
              </DialogHeader>

              <div className="space-y-4 text-xs mt-4">
                {selectedRecord.description && (
                  <div className="p-3 rounded-lg bg-muted/50 border">
                    <div className="font-semibold text-foreground mb-1">Summary</div>
                    <p className="text-muted-foreground leading-relaxed">{selectedRecord.description}</p>
                  </div>
                )}

                <div>
                  <div className="font-semibold text-foreground mb-2">Structured Metadata Attributes</div>
                  <pre className="p-3 rounded-lg bg-muted text-[11px] font-mono overflow-x-auto max-h-60 border">
                    {JSON.stringify(selectedRecord.metadata, null, 2)}
                  </pre>
                </div>

                <div className="flex items-center justify-end gap-2 pt-2 border-t">
                  <a
                    href={selectedRecord.external_url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90"
                  >
                    View Official Database Entry
                    <ExternalLink className="h-3.5 w-3.5" />
                  </a>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
