"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  AlertCircle,
  Check,
  Copy,
  Database,
  Dna,
  ExternalLink,
  FileText,
  Globe,
  Info,
  Layers,
  MapPin,
  RefreshCw,
  Search,
  Sparkles,
  X,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError, NetworkError, apiRequest } from "@/lib/api";

// Biological data contracts matching FastAPI backend schemas
interface GenomicLocation {
  chromosome: string | null;
  start: number | null;
  end: number | null;
  strand: number | null;
  ensembl_gene_id: string | null;
}

interface DatabaseReference {
  database: string;
  identifier: string;
  url: string;
  description: string | null;
}

interface GeneSearchResult {
  id: string;
  symbol: string;
  name: string | null;
  species: string;
  taxid: number | null;
  entrez_id: string | null;
  ensembl_id: string | null;
  chromosome: string | null;
  type_of_gene: string | null;
  aliases: string[];
  score: number | null;
}

interface GeneSearchResponse {
  query: string;
  species: string;
  total: number;
  results: GeneSearchResult[];
  source: string;
}

interface GeneDetailResponse {
  id: string;
  symbol: string;
  name: string | null;
  species: string;
  taxid: number | null;
  entrez_id: string | null;
  ensembl_id: string | null;
  type_of_gene: string | null;
  chromosome: string | null;
  genomic_location: GenomicLocation | null;
  aliases: string[];
  summary: string | null;
  references: DatabaseReference[];
  source: string;
  retrieved_at: string;
  cached: boolean;
}

const POPULAR_GENES = [
  { symbol: "BRCA1", label: "BRCA1 (DNA repair)" },
  { symbol: "TP53", label: "TP53 (Tumor suppressor)" },
  { symbol: "EGFR", label: "EGFR (Growth factor)" },
  { symbol: "APOE", label: "APOE (Lipid metabolism)" },
  { symbol: "TNF", label: "TNF (Inflammatory)" },
  { symbol: "MTOR", label: "MTOR (Kinase / Signaling)" },
  { symbol: "ACE2", label: "ACE2 (Viral receptor)" },
];

const SPECIES_OPTIONS = [
  { value: "human", label: "Homo sapiens (Human)" },
  { value: "mouse", label: "Mus musculus (Mouse)" },
  { value: "rat", label: "Rattus norvegicus (Rat)" },
  { value: "zebrafish", label: "Danio rerio (Zebrafish)" },
  { value: "fruitfly", label: "Drosophila melanogaster (Fruit fly)" },
  { value: "nematode", label: "Caenorhabditis elegans (Nematode)" },
  { value: "yeast", label: "Saccharomyces cerevisiae (Yeast)" },
  { value: "all", label: "All Organisms" },
];

function GeneIntelligenceContent() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q") || "";

  // Query states
  const [query, setQuery] = useState(initialQuery);
  const [species, setSpecies] = useState("human");

  // Search Results state
  const [searching, setSearching] = useState(false);
  const [searchResponse, setSearchResponse] = useState<GeneSearchResponse | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);

  // Inspected Gene Detail state
  const [selectedGeneId, setSelectedGeneId] = useState<string | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [geneDetail, setGeneDetail] = useState<GeneDetailResponse | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  // Feedback states
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // Copy helper
  const handleCopy = (text: string, key: string) => {
    if (navigator?.clipboard) {
      navigator.clipboard.writeText(text);
      setCopiedKey(key);
      setTimeout(() => setCopiedKey(null), 2000);
    }
  };

  // Perform gene search
  const performSearch = useCallback(
    async (searchTerm: string, targetSpecies: string) => {
      const trimmed = searchTerm.trim();
      if (!trimmed) return;

      setSearching(true);
      setSearchError(null);

      try {
        const data = await apiRequest<GeneSearchResponse>("/api/v1/genes/search", {
          params: {
            q: trimmed,
            species: targetSpecies,
            limit: 20,
          },
        });
        setSearchResponse(data);

        // Auto-select first result if available and none selected or previous search
        if (data.results.length > 0) {
          const firstHit = data.results[0];
          setSelectedGeneId(firstHit.symbol || firstHit.id);
        } else {
          setSelectedGeneId(null);
          setGeneDetail(null);
        }
      } catch (err) {
        if (err instanceof ApiError) {
          setSearchError(`Biological API error (${err.status}): ${err.message}`);
        } else if (err instanceof NetworkError) {
          setSearchError(`Connection failed: ${err.message}`);
        } else {
          setSearchError("Failed to search genes in biological databases.");
        }
        setSearchResponse(null);
      } finally {
        setSearching(false);
      }
    },
    []
  );

  // Fetch gene details
  const fetchGeneDetail = useCallback(
    async (geneId: string, force = false) => {
      if (!geneId) return;

      if (force) {
        setRefreshing(true);
      } else {
        setDetailLoading(true);
      }
      setDetailError(null);

      try {
        const data = await apiRequest<GeneDetailResponse>(`/api/v1/genes/${encodeURIComponent(geneId)}`, {
          params: force ? { force_refresh: true } : undefined,
        });
        setGeneDetail(data);
      } catch (err) {
        if (err instanceof ApiError) {
          setDetailError(`Error ${err.status}: ${err.message}`);
        } else if (err instanceof NetworkError) {
          setDetailError(err.message);
        } else {
          setDetailError("Failed to load comprehensive gene record.");
        }
        setGeneDetail(null);
      } finally {
        setDetailLoading(false);
        setRefreshing(false);
      }
    },
    []
  );

  // Trigger search on form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    performSearch(query, species);
  };

  // Trigger search on popular gene click
  const handleSelectQuickGene = (symbol: string) => {
    setQuery(symbol);
    performSearch(symbol, species);
  };

  // Inspect specific gene from results
  const handleSelectHit = (geneId: string) => {
    setSelectedGeneId(geneId);
    fetchGeneDetail(geneId, false);
  };

  // Initial load if query param present
  useEffect(() => {
    if (!initialQuery) return;
    let ignore = false;

    async function runInitialQuery() {
      try {
        const data = await apiRequest<GeneSearchResponse>("/api/v1/genes/search", {
          params: { q: initialQuery.trim(), species: "human", limit: 20 },
        });
        if (!ignore) {
          setSearchResponse(data);
          if (data.results.length > 0) {
            const firstHit = data.results[0];
            const firstId = firstHit.symbol || firstHit.id;
            setSelectedGeneId(firstId);
            const detailData = await apiRequest<GeneDetailResponse>(
              `/api/v1/genes/${encodeURIComponent(firstId)}`
            );
            if (!ignore) {
              setGeneDetail(detailData);
            }
          }
        }
      } catch {
        // Fail gracefully on initial query
      }
    }

    runInitialQuery();
    return () => {
      ignore = true;
    };
  }, [initialQuery]);

  return (
    <div className="space-y-6 p-6 md:p-8">
      {/* 1. Header & Overview */}
      <div className="relative overflow-hidden rounded-xl border border-border/80 bg-gradient-to-r from-card via-card to-primary/5 p-6 md:p-8 shadow-xs">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="max-w-3xl space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline" className="gap-1 border-primary/30 text-primary text-[11px]">
                <Dna className="h-3 w-3" />
                <span>Genomic Intelligence</span>
              </Badge>
              <Badge variant="secondary" className="text-[11px] font-normal">
                Direct MyGene.info & NCBI Entrez API
              </Badge>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground md:text-3xl">
              Gene Intelligence Explorer
            </h1>
            <p className="text-sm leading-relaxed text-muted-foreground">
              Search verified biological gene repositories by symbol, Entrez ID, Ensembl ID, or functional keywords.
              Inspect genomic coordinates, transcript architecture, curated summaries, and cross-references cached in PostgreSQL.
            </p>
          </div>

          <div className="flex items-center gap-2 self-start lg:self-auto">
            <div className="rounded-lg border border-border bg-background/80 px-3 py-2 text-xs text-muted-foreground backdrop-blur-xs">
              <div className="flex items-center gap-1.5 font-medium text-foreground">
                <Database className="h-3.5 w-3.5 text-primary" />
                <span>Source Attribution</span>
              </div>
              <p className="mt-0.5 text-[11px]">NCBI Gene • Ensembl • HGNC • OMIM</p>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Search Bar & Organism Filters */}
      <Card className="shadow-xs border-border/80">
        <CardContent className="p-4 sm:p-6 space-y-4">
          <form onSubmit={handleSubmit} className="flex flex-col gap-3 sm:flex-row">
            {/* Organism Selector */}
            <div className="w-full sm:w-56 shrink-0">
              <label htmlFor="species-select" className="sr-only">Organism Filter</label>
              <select
                id="species-select"
                value={species}
                onChange={(e) => setSpecies(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-card px-3 py-2 text-xs font-medium text-foreground shadow-xs transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              >
                {SPECIES_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Query Input */}
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Search symbol, Entrez ID, Ensembl ID, or keyword (e.g. BRCA1, TP53, kinase)..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="pl-9 pr-9 text-xs sm:text-sm h-10"
              />
              {query && (
                <button
                  type="button"
                  onClick={() => setQuery("")}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={searching || !query.trim()}
              className="h-10 px-5 gap-2 text-xs font-semibold shrink-0"
            >
              {searching ? (
                <>
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                  <span>Searching...</span>
                </>
              ) : (
                <>
                  <Search className="h-3.5 w-3.5" />
                  <span>Search Biological DB</span>
                </>
              )}
            </Button>
          </form>

          {/* Quick Gene Selector Pills */}
          <div className="flex flex-wrap items-center gap-1.5 pt-1">
            <span className="text-[11px] font-medium text-muted-foreground mr-1">Popular Targets:</span>
            {POPULAR_GENES.map((gene) => (
              <button
                key={gene.symbol}
                type="button"
                onClick={() => handleSelectQuickGene(gene.symbol)}
                className="inline-flex items-center gap-1 rounded-full border border-border/80 bg-muted/40 px-2.5 py-1 text-[11px] font-medium text-muted-foreground hover:border-primary/40 hover:bg-primary/5 hover:text-primary transition-all"
              >
                <Sparkles className="h-2.5 w-2.5" />
                <span>{gene.symbol}</span>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 3. Search Error Notification */}
      {searchError && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive flex items-start gap-3">
          <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="font-semibold text-xs">Search Failed</p>
            <p className="text-xs opacity-90">{searchError}</p>
          </div>
        </div>
      )}

      {/* 4. Results & Detail Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Left: Search Results List (5 cols on lg) */}
        <div className="lg:col-span-5 space-y-4">
          <Card className="border-border/80 shadow-xs">
            <CardHeader className="p-4 border-b border-border/60">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-sm font-semibold">Matching Biological Hits</CardTitle>
                  <CardDescription className="text-xs">
                    {searchResponse
                      ? `${searchResponse.total} hits found for "${searchResponse.query}"`
                      : "Search genes to populate results"}
                  </CardDescription>
                </div>
                {searchResponse && (
                  <Badge variant="secondary" className="text-[10px]">
                    {searchResponse.results.length} shown
                  </Badge>
                )}
              </div>
            </CardHeader>

            <CardContent className="p-2 divide-y divide-border/40 max-h-[620px] overflow-y-auto">
              {searching ? (
                <div className="space-y-3 p-4">
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Skeleton className="h-5 w-16" />
                        <Skeleton className="h-4 w-32" />
                      </div>
                      <Skeleton className="h-3 w-48" />
                    </div>
                  ))}
                </div>
              ) : searchResponse && searchResponse.results.length > 0 ? (
                searchResponse.results.map((hit) => {
                  const hitKey = hit.symbol || hit.id;
                  const isSelected = selectedGeneId === hitKey || selectedGeneId === hit.id;
                  return (
                    <div
                      key={hit.id}
                      onClick={() => handleSelectHit(hit.symbol || hit.id)}
                      className={`group cursor-pointer rounded-lg p-3 transition-colors ${isSelected
                          ? "bg-primary/10 border-primary/30 border"
                          : "hover:bg-muted/60"
                        }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-sm text-foreground group-hover:text-primary transition-colors">
                            {hit.symbol}
                          </span>
                          {hit.type_of_gene && (
                            <Badge variant="outline" className="text-[10px] py-0 px-1.5 h-4 border-border">
                              {hit.type_of_gene}
                            </Badge>
                          )}
                        </div>
                        {hit.chromosome && (
                          <span className="text-[11px] font-mono text-muted-foreground flex items-center gap-1">
                            <MapPin className="h-2.5 w-2.5" />
                            Chr {hit.chromosome}
                          </span>
                        )}
                      </div>

                      {hit.name && (
                        <p className="mt-1 text-xs text-muted-foreground line-clamp-1">
                          {hit.name}
                        </p>
                      )}

                      <div className="mt-2 flex flex-wrap items-center gap-2 text-[10px] text-muted-foreground font-mono">
                        {hit.entrez_id && <span>Entrez: {hit.entrez_id}</span>}
                        {hit.ensembl_id && <span>Ensembl: {hit.ensembl_id}</span>}
                        {hit.taxid && <span>TaxID: {hit.taxid}</span>}
                      </div>

                      {hit.aliases && hit.aliases.length > 0 && (
                        <div className="mt-1.5 flex flex-wrap gap-1">
                          {hit.aliases.slice(0, 3).map((a) => (
                            <span
                              key={a}
                              className="rounded bg-muted px-1.5 py-0.5 text-[9px] text-muted-foreground"
                            >
                              {a}
                            </span>
                          ))}
                          {hit.aliases.length > 3 && (
                            <span className="text-[9px] text-muted-foreground">
                              +{hit.aliases.length - 3} more
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })
              ) : searchResponse && searchResponse.results.length === 0 ? (
                <div className="p-8 text-center text-muted-foreground space-y-2">
                  <Info className="h-8 w-8 mx-auto text-muted-foreground/60" />
                  <p className="text-xs font-semibold">No genes matched your criteria</p>
                  <p className="text-[11px] text-muted-foreground max-w-xs mx-auto">
                    Try broadening your search term or selecting &ldquo;All Organisms&rdquo; in the dropdown above.
                  </p>
                </div>
              ) : (
                <div className="p-8 text-center text-muted-foreground space-y-2">
                  <Dna className="h-8 w-8 mx-auto text-muted-foreground/50" />
                  <p className="text-xs font-medium">No active search</p>
                  <p className="text-[11px] text-muted-foreground max-w-xs mx-auto">
                    Enter a gene symbol like <span className="font-mono text-foreground">BRCA1</span> or select one of the popular targets above.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right: Comprehensive Gene Record Inspection (7 cols on lg) */}
        <div className="lg:col-span-7 space-y-4">
          {detailError && (
            <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-xs text-destructive flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{detailError}</span>
              </div>
              {selectedGeneId && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => fetchGeneDetail(selectedGeneId, true)}
                  className="h-7 text-[11px]"
                >
                  Retry
                </Button>
              )}
            </div>
          )}

          {detailLoading ? (
            <Card className="border-border/80 p-6 space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-2">
                  <Skeleton className="h-7 w-32" />
                  <Skeleton className="h-4 w-64" />
                </div>
                <Skeleton className="h-8 w-24" />
              </div>
              <Skeleton className="h-24 w-full" />
              <div className="grid grid-cols-2 gap-4">
                <Skeleton className="h-20 w-full" />
                <Skeleton className="h-20 w-full" />
              </div>
            </Card>
          ) : geneDetail ? (
            <Card className="border-border/80 shadow-xs">
              {/* Record Top Bar */}
              <CardHeader className="p-5 border-b border-border/60">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <h2 className="text-xl font-bold text-foreground tracking-tight">
                        {geneDetail.symbol}
                      </h2>
                      {geneDetail.type_of_gene && (
                        <Badge variant="outline" className="text-xs border-primary/30 text-primary">
                          {geneDetail.type_of_gene}
                        </Badge>
                      )}
                      <Badge variant="secondary" className="text-xs">
                        {geneDetail.species}
                      </Badge>
                    </div>
                    {geneDetail.name && (
                      <p className="text-sm text-muted-foreground font-medium">
                        {geneDetail.name}
                      </p>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <Badge
                      variant={geneDetail.cached ? "outline" : "default"}
                      className={`text-[10px] gap-1 ${geneDetail.cached
                          ? "border-emerald-500/30 text-emerald-600 dark:text-emerald-400 bg-emerald-500/10"
                          : "bg-blue-600 text-white"
                        }`}
                    >
                      <Database className="h-3 w-3" />
                      <span>{geneDetail.cached ? "PostgreSQL Cache" : "Live Biological API"}</span>
                    </Badge>

                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => fetchGeneDetail(geneDetail.id || geneDetail.symbol, true)}
                      disabled={refreshing}
                      className="h-7 px-2.5 text-[11px] gap-1 text-muted-foreground hover:text-foreground"
                      title="Fetch fresh biological record bypassing cache"
                    >
                      <RefreshCw className={`h-3 w-3 ${refreshing ? "animate-spin" : ""}`} />
                      <span>{refreshing ? "Refreshing..." : "Re-sync"}</span>
                    </Button>
                  </div>
                </div>
              </CardHeader>

              <CardContent className="p-5 space-y-6">
                {/* 1. Curated Functional Summary */}
                <div className="space-y-2">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-foreground">
                    <FileText className="h-3.5 w-3.5 text-primary" />
                    <span>Biological Function & Summary</span>
                  </div>
                  {geneDetail.summary ? (
                    <div className="rounded-lg bg-muted/40 border border-border/60 p-3.5 text-xs leading-relaxed text-muted-foreground">
                      {geneDetail.summary}
                    </div>
                  ) : (
                    <p className="text-xs italic text-muted-foreground">
                      No curated narrative summary currently cataloged for this gene locus in primary repositories.
                    </p>
                  )}
                </div>

                {/* 2. Genomic Coordinates Card */}
                <div className="space-y-2">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-foreground">
                    <MapPin className="h-3.5 w-3.5 text-primary" />
                    <span>Genomic Architecture & Locus Coordinates</span>
                  </div>

                  <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                    <div className="rounded-lg border border-border/80 bg-card p-3">
                      <span className="text-[10px] uppercase font-semibold text-muted-foreground">Chromosome</span>
                      <p className="mt-1 text-sm font-mono font-bold text-foreground">
                        {geneDetail.chromosome ? `Chr ${geneDetail.chromosome}` : "Not mapped"}
                      </p>
                    </div>

                    <div className="rounded-lg border border-border/80 bg-card p-3">
                      <span className="text-[10px] uppercase font-semibold text-muted-foreground">Genomic Start</span>
                      <p className="mt-1 text-sm font-mono font-bold text-foreground">
                        {geneDetail.genomic_location?.start
                          ? geneDetail.genomic_location.start.toLocaleString()
                          : "—"}
                      </p>
                    </div>

                    <div className="rounded-lg border border-border/80 bg-card p-3">
                      <span className="text-[10px] uppercase font-semibold text-muted-foreground">Genomic End</span>
                      <p className="mt-1 text-sm font-mono font-bold text-foreground">
                        {geneDetail.genomic_location?.end
                          ? geneDetail.genomic_location.end.toLocaleString()
                          : "—"}
                      </p>
                    </div>

                    <div className="rounded-lg border border-border/80 bg-card p-3">
                      <span className="text-[10px] uppercase font-semibold text-muted-foreground">Strand</span>
                      <p className="mt-1 text-sm font-mono font-bold text-foreground">
                        {geneDetail.genomic_location?.strand === 1
                          ? "+ (Forward)"
                          : geneDetail.genomic_location?.strand === -1
                            ? "- (Reverse)"
                            : "Unspecified"}
                      </p>
                    </div>
                  </div>
                </div>

                {/* 3. Primary Identifiers with Copy Buttons */}
                <div className="space-y-2">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-foreground">
                    <Layers className="h-3.5 w-3.5 text-primary" />
                    <span>Biological Accession Identifiers</span>
                  </div>

                  <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
                    {/* Entrez Gene ID */}
                    <div className="flex items-center justify-between rounded-lg border border-border bg-card p-2.5 text-xs">
                      <div>
                        <span className="text-[10px] font-semibold text-muted-foreground">NCBI Entrez ID</span>
                        <p className="font-mono font-bold text-foreground">
                          {geneDetail.entrez_id || "—"}
                        </p>
                      </div>
                      {geneDetail.entrez_id && (
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={() => handleCopy(geneDetail.entrez_id!, "entrez")}
                          className="h-7 w-7 text-muted-foreground hover:text-foreground"
                          title="Copy Entrez ID"
                        >
                          {copiedKey === "entrez" ? (
                            <Check className="h-3.5 w-3.5 text-emerald-500" />
                          ) : (
                            <Copy className="h-3.5 w-3.5" />
                          )}
                        </Button>
                      )}
                    </div>

                    {/* Ensembl Gene ID */}
                    <div className="flex items-center justify-between rounded-lg border border-border bg-card p-2.5 text-xs">
                      <div>
                        <span className="text-[10px] font-semibold text-muted-foreground">Ensembl Gene ID</span>
                        <p className="font-mono font-bold text-foreground">
                          {geneDetail.ensembl_id || "—"}
                        </p>
                      </div>
                      {geneDetail.ensembl_id && (
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={() => handleCopy(geneDetail.ensembl_id!, "ensembl")}
                          className="h-7 w-7 text-muted-foreground hover:text-foreground"
                          title="Copy Ensembl ID"
                        >
                          {copiedKey === "ensembl" ? (
                            <Check className="h-3.5 w-3.5 text-emerald-500" />
                          ) : (
                            <Copy className="h-3.5 w-3.5" />
                          )}
                        </Button>
                      )}
                    </div>
                  </div>
                </div>

                {/* 4. Synonyms & Aliases */}
                {geneDetail.aliases && geneDetail.aliases.length > 0 && (
                  <div className="space-y-2">
                    <span className="text-xs font-semibold text-foreground">Approved Aliases & Synonyms</span>
                    <div className="flex flex-wrap gap-1.5">
                      {geneDetail.aliases.map((alias) => (
                        <span
                          key={alias}
                          className="rounded-md border border-border/80 bg-muted/40 px-2 py-0.5 font-mono text-[11px] text-muted-foreground"
                        >
                          {alias}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* 5. Verified Database Cross-References */}
                <div className="space-y-2 pt-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5 text-xs font-semibold text-foreground">
                      <Globe className="h-3.5 w-3.5 text-primary" />
                      <span>Cross-Database Biological Portals</span>
                    </div>
                    <span className="text-[11px] text-muted-foreground">
                      {geneDetail.references.length} direct links
                    </span>
                  </div>

                  <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
                    {geneDetail.references.map((ref) => (
                      <a
                        key={`${ref.database}-${ref.identifier}`}
                        href={ref.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="group flex items-start justify-between rounded-lg border border-border/80 bg-card p-3 hover:border-primary/40 hover:bg-primary/5 transition-all"
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-1.5">
                            <span className="font-semibold text-xs text-foreground group-hover:text-primary transition-colors">
                              {ref.database}
                            </span>
                            <span className="font-mono text-[10px] text-muted-foreground">
                              ({ref.identifier})
                            </span>
                          </div>
                          {ref.description && (
                            <p className="text-[11px] text-muted-foreground line-clamp-1">
                              {ref.description}
                            </p>
                          )}
                        </div>
                        <ExternalLink className="h-3.5 w-3.5 text-muted-foreground group-hover:text-primary transition-colors shrink-0 mt-0.5" />
                      </a>
                    ))}
                  </div>
                </div>

                {/* 6. Provenance Footer */}
                <div className="pt-3 border-t border-border/60 flex flex-wrap items-center justify-between gap-2 text-[11px] text-muted-foreground">
                  <span>Data Source: {geneDetail.source}</span>
                  <span>Retrieved: {new Date(geneDetail.retrieved_at).toLocaleString()}</span>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card className="border-border/80 p-12 text-center text-muted-foreground shadow-xs">
              <Dna className="h-10 w-10 mx-auto text-muted-foreground/40 mb-3" />
              <h3 className="text-sm font-semibold text-foreground">No Gene Selected</h3>
              <p className="mt-1 text-xs text-muted-foreground max-w-sm mx-auto">
                Search for an organism target or select a gene hit from the left column to inspect its complete molecular profile.
              </p>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

export default function GeneIntelligencePage() {
  return (
    <Suspense
      fallback={
        <div className="p-8 space-y-4">
          <Skeleton className="h-32 w-full rounded-xl" />
          <Skeleton className="h-16 w-full rounded-xl" />
          <div className="grid grid-cols-12 gap-6">
            <Skeleton className="col-span-5 h-96 rounded-xl" />
            <Skeleton className="col-span-7 h-96 rounded-xl" />
          </div>
        </div>
      }
    >
      <GeneIntelligenceContent />
    </Suspense>
  );
}
