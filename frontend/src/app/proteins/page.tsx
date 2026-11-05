"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  Activity,
  AlertCircle,
  Box,
  Check,
  Copy,
  Database,
  Download,
  ExternalLink,
  FileText,
  Globe,
  Info,
  RefreshCw,
  Search,
  ShieldCheck,
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ApiError, NetworkError, apiRequest } from "@/lib/api";

// Biological data contracts matching FastAPI backend schemas
interface ProteinSearchResult {
  accession: string;
  entry_name: string | null;
  protein_name: string;
  gene_name: string | null;
  organism: string;
  taxid: number | null;
  length: number;
  reviewed: boolean;
  score: number | null;
}

interface ProteinSearchResponse {
  query: string;
  species: string;
  total: number;
  results: ProteinSearchResult[];
  source: string;
}

interface DatabaseReference {
  database: string;
  identifier: string;
  url: string;
  description: string | null;
}

interface ProteinDetailResponse {
  accession: string;
  entry_name: string | null;
  protein_name: string;
  gene_name: string | null;
  organism: string;
  taxid: number | null;
  sequence_length: number;
  sequence: string;
  mass_da: number | null;
  function_summary: string | null;
  subcellular_location: string | null;
  protein_existence: string | null;
  ptms: string[];
  features_summary: Record<string, number>;
  pdb_structures_count: number;
  has_alphafold: boolean;
  references: DatabaseReference[];
  source: string;
  retrieved_at: string;
  cached: boolean;
}

interface AminoAcidComposition {
  counts: Record<string, number>;
  percentages: Record<string, number>;
  non_canonical: Record<string, number>;
}

interface PhysicochemicalProperties {
  theoretical_molecular_weight_da: number | null;
  isoelectric_point: number | null;
  aromaticity: number | null;
  instability_index: number | null;
  is_stable: boolean | null;
  gravy_score: number | null;
  charge_at_ph7: number | null;
  computational_notes: string[];
}

interface ProteinSequenceAnalysisResponse {
  accession: string;
  protein_name: string;
  length: number;
  sequence: string;
  fasta: string;
  composition: AminoAcidComposition;
  properties: PhysicochemicalProperties;
  is_canonical_only: boolean;
  source: string;
}

interface PdbStructure {
  pdb_id: string;
  title: string | null;
  method: string;
  resolution_angstrom: number | null;
  chains: string | null;
  deposition_date: string | null;
  url: string;
  is_experimental: boolean;
}

interface AlphaFoldStructure {
  entry_id: string;
  accession: string;
  global_plddt: number | null;
  confidence_category: string | null;
  pdb_url: string | null;
  cif_url: string | null;
  url: string;
  is_experimental: boolean;
  prediction_note: string;
}

interface ProteinStructuresResponse {
  accession: string;
  protein_name: string;
  experimental_structures: PdbStructure[];
  predicted_structure: AlphaFoldStructure | null;
  experimental_count: number;
  predicted_available: boolean;
  source: string;
}

const POPULAR_PROTEINS = [
  { accession: "P68871", label: "HBB (Hemoglobin beta)" },
  { accession: "P04637", label: "TP53 (Tumor protein p53)" },
  { accession: "P00533", label: "EGFR (EGF receptor)" },
  { accession: "P01308", label: "INS (Insulin)" },
  { accession: "P02768", label: "ALB (Serum albumin)" },
  { accession: "P38398", label: "BRCA1 (DNA repair)" },
  { accession: "Q9BYF1", label: "ACE2 (Angiotensin receptor)" },
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

function ProteinIntelligenceContent() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q") || "";

  // Query states
  const [query, setQuery] = useState(initialQuery);
  const [species, setSpecies] = useState("human");

  // Search Results state
  const [searching, setSearching] = useState(false);
  const [searchResponse, setSearchResponse] = useState<ProteinSearchResponse | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);

  // Inspected Protein Detail state
  const [selectedAccession, setSelectedAccession] = useState<string | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [proteinDetail, setProteinDetail] = useState<ProteinDetailResponse | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  // Additional Tabs state (Sequence Analysis & Structures)
  const [sequenceLoading, setSequenceLoading] = useState(false);
  const [sequenceData, setSequenceData] = useState<ProteinSequenceAnalysisResponse | null>(null);
  const [structuresLoading, setStructuresLoading] = useState(false);
  const [structuresData, setStructuresData] = useState<ProteinStructuresResponse | null>(null);
  const [activeTab, setActiveTab] = useState("overview");

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

  // Download FASTA helper
  const handleDownloadFasta = (fasta: string, filename: string) => {
    const blob = new Blob([fasta], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${filename}.fasta`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Fetch protein detail and optional sub-resources
  const fetchProteinDetail = useCallback(
    async (acc: string, force = false) => {
      if (!acc) return;

      if (force) {
        setRefreshing(true);
      } else {
        setDetailLoading(true);
      }
      setDetailError(null);

      try {
        const detail = await apiRequest<ProteinDetailResponse>(
          `/api/v1/proteins/${encodeURIComponent(acc)}`,
          { params: force ? { force_refresh: true } : undefined }
        );
        setProteinDetail(detail);

        // Concurrently fetch sequence analysis & 3D structures
        setSequenceLoading(true);
        setStructuresLoading(true);

        const [seqRes, structRes] = await Promise.allSettled([
          apiRequest<ProteinSequenceAnalysisResponse>(`/api/v1/proteins/${encodeURIComponent(acc)}/sequence`),
          apiRequest<ProteinStructuresResponse>(`/api/v1/proteins/${encodeURIComponent(acc)}/structures`),
        ]);

        if (seqRes.status === "fulfilled") {
          setSequenceData(seqRes.value);
        } else {
          setSequenceData(null);
        }

        if (structRes.status === "fulfilled") {
          setStructuresData(structRes.value);
        } else {
          setStructuresData(null);
        }
      } catch (err) {
        if (err instanceof ApiError) {
          setDetailError(`Error ${err.status}: ${err.message}`);
        } else if (err instanceof NetworkError) {
          setDetailError(err.message);
        } else {
          setDetailError("Failed to retrieve protein record from biological database.");
        }
        setProteinDetail(null);
      } finally {
        setDetailLoading(false);
        setRefreshing(false);
        setSequenceLoading(false);
        setStructuresLoading(false);
      }
    },
    []
  );

  // Perform protein search
  const performSearch = useCallback(
    async (searchTerm: string, targetSpecies: string) => {
      const trimmed = searchTerm.trim();
      if (!trimmed) return;

      setSearching(true);
      setSearchError(null);

      try {
        const data = await apiRequest<ProteinSearchResponse>("/api/v1/proteins/search", {
          params: {
            q: trimmed,
            species: targetSpecies,
            limit: 20,
          },
        });
        setSearchResponse(data);

        // Auto-select and fetch first result if available
        if (data.results.length > 0) {
          const firstHit = data.results[0];
          setSelectedAccession(firstHit.accession);
          await fetchProteinDetail(firstHit.accession, false);
        } else {
          setSelectedAccession(null);
          setProteinDetail(null);
          setSequenceData(null);
          setStructuresData(null);
        }
      } catch (err) {
        if (err instanceof ApiError) {
          setSearchError(`UniProtKB API error (${err.status}): ${err.message}`);
        } else if (err instanceof NetworkError) {
          setSearchError(`Connection failed: ${err.message}`);
        } else {
          setSearchError("Failed to search proteins in biological databases.");
        }
        setSearchResponse(null);
      } finally {
        setSearching(false);
      }
    },
    [fetchProteinDetail]
  );

  // Trigger search on form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    performSearch(query, species);
  };

  // Trigger search on popular protein click
  const handleSelectQuickProtein = (acc: string) => {
    setQuery(acc);
    performSearch(acc, species);
  };

  // Inspect specific protein from results list
  const handleSelectHit = (acc: string) => {
    setSelectedAccession(acc);
    fetchProteinDetail(acc, false);
  };

  // Initial load if query param present
  useEffect(() => {
    if (!initialQuery) return;
    let ignore = false;

    async function runInitialQuery() {
      try {
        const searchData = await apiRequest<ProteinSearchResponse>("/api/v1/proteins/search", {
          params: {
            q: initialQuery.trim(),
            species: "human",
            limit: 20,
          },
        });
        if (!ignore) {
          setSearchResponse(searchData);
          if (searchData.results.length > 0) {
            const firstAcc = searchData.results[0].accession;
            setSelectedAccession(firstAcc);
            const detailData = await apiRequest<ProteinDetailResponse>(
              `/api/v1/proteins/${encodeURIComponent(firstAcc)}`
            );
            if (!ignore) {
              setProteinDetail(detailData);
            }
          }
        }
      } catch (err) {
        if (!ignore) {
          if (err instanceof ApiError) {
            setSearchError(`UniProtKB API error (${err.status}): ${err.message}`);
          } else {
            setSearchError("Failed to load initial protein query.");
          }
        }
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
                <Activity className="h-3 w-3" />
                <span>Proteomic Intelligence</span>
              </Badge>
              <Badge variant="secondary" className="text-[11px] font-normal">
                UniProtKB • RCSB PDB • AlphaFold DB
              </Badge>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground md:text-3xl">
              Protein Intelligence Explorer
            </h1>
            <p className="text-sm leading-relaxed text-muted-foreground">
              Investigate curated polypeptide annotations, genuine Biopython sequence properties, and macromolecular structures.
              Contrast experimental X-ray/Cryo-EM structures from RCSB PDB with computational AI predictions from AlphaFold.
            </p>
          </div>

          <div className="flex items-center gap-2 self-start lg:self-auto">
            <div className="rounded-lg border border-border bg-background/80 px-3 py-2 text-xs text-muted-foreground backdrop-blur-xs">
              <div className="flex items-center gap-1.5 font-medium text-foreground">
                <Database className="h-3.5 w-3.5 text-primary" />
                <span>Authoritative Repositories</span>
              </div>
              <p className="mt-0.5 text-[11px]">UniProtKB • RCSB PDB • AlphaFold DB • GeneCards</p>
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
              <label htmlFor="protein-species-select" className="sr-only">Organism Filter</label>
              <select
                id="protein-species-select"
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
                placeholder="Search protein name, UniProt accession, gene symbol, or keyword (e.g. hemoglobin, P68871, TP53)..."
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
                  <span>Search UniProtKB</span>
                </>
              )}
            </Button>
          </form>

          {/* Quick Target Chips */}
          <div className="flex flex-wrap items-center gap-1.5 pt-1">
            <span className="text-[11px] font-medium text-muted-foreground mr-1">Curated Benchmarks:</span>
            {POPULAR_PROTEINS.map((p) => (
              <button
                key={p.accession}
                type="button"
                onClick={() => handleSelectQuickProtein(p.accession)}
                className="inline-flex items-center gap-1 rounded-full border border-border/80 bg-muted/40 px-2.5 py-1 text-[11px] font-medium text-muted-foreground hover:border-primary/40 hover:bg-primary/5 hover:text-primary transition-all"
              >
                <Sparkles className="h-2.5 w-2.5" />
                <span>{p.label}</span>
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
                  <CardTitle className="text-sm font-semibold">UniProtKB Biological Hits</CardTitle>
                  <CardDescription className="text-xs">
                    {searchResponse
                      ? `${searchResponse.total} proteins discovered for "${searchResponse.query}"`
                      : "Search proteins to view biological records"}
                  </CardDescription>
                </div>
                {searchResponse && (
                  <Badge variant="secondary" className="text-[10px]">
                    {searchResponse.results.length} shown
                  </Badge>
                )}
              </div>
            </CardHeader>

            <CardContent className="p-2 divide-y divide-border/40 max-h-[660px] overflow-y-auto">
              {searching ? (
                <div className="space-y-3 p-4">
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Skeleton className="h-5 w-20" />
                        <Skeleton className="h-4 w-36" />
                      </div>
                      <Skeleton className="h-3 w-48" />
                    </div>
                  ))}
                </div>
              ) : searchResponse && searchResponse.results.length > 0 ? (
                searchResponse.results.map((hit) => {
                  const isSelected = selectedAccession === hit.accession;
                  return (
                    <div
                      key={hit.accession}
                      onClick={() => handleSelectHit(hit.accession)}
                      className={`group cursor-pointer rounded-lg p-3 transition-colors ${
                        isSelected
                          ? "bg-primary/10 border-primary/30 border"
                          : "hover:bg-muted/60"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-bold text-sm text-foreground group-hover:text-primary transition-colors">
                            {hit.accession}
                          </span>
                          <Badge
                            variant={hit.reviewed ? "default" : "outline"}
                            className={`text-[10px] py-0 px-1.5 h-4 ${
                              hit.reviewed
                                ? "bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/30"
                                : "text-muted-foreground border-border"
                            }`}
                          >
                            {hit.reviewed ? "Swiss-Prot" : "TrEMBL"}
                          </Badge>
                        </div>
                        <span className="text-[11px] font-mono text-muted-foreground">
                          {hit.length} aa
                        </span>
                      </div>

                      <p className="mt-1 text-xs font-medium text-foreground line-clamp-1">
                        {hit.protein_name}
                      </p>

                      <div className="mt-2 flex flex-wrap items-center gap-2 text-[10px] text-muted-foreground font-mono">
                        {hit.gene_name && <span>Gene: {hit.gene_name}</span>}
                        {hit.entry_name && <span>Entry: {hit.entry_name}</span>}
                        <span>{hit.organism}</span>
                      </div>
                    </div>
                  );
                })
              ) : searchResponse && searchResponse.results.length === 0 ? (
                <div className="p-8 text-center text-muted-foreground space-y-2">
                  <Info className="h-8 w-8 mx-auto text-muted-foreground/60" />
                  <p className="text-xs font-semibold">No proteins matched your criteria</p>
                  <p className="text-[11px] text-muted-foreground max-w-xs mx-auto">
                    Try broadening your query term or switching organism to &ldquo;All Organisms&rdquo;.
                  </p>
                </div>
              ) : (
                <div className="p-8 text-center text-muted-foreground space-y-2">
                  <Activity className="h-8 w-8 mx-auto text-muted-foreground/50" />
                  <p className="text-xs font-medium">No active search</p>
                  <p className="text-[11px] text-muted-foreground max-w-xs mx-auto">
                    Enter a protein name, gene symbol like <span className="font-mono text-foreground">HBB</span>, or accession <span className="font-mono text-foreground">P68871</span>.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right: Comprehensive Protein Record Workspace (7 cols on lg) */}
        <div className="lg:col-span-7 space-y-4">
          {detailError && (
            <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-xs text-destructive flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{detailError}</span>
              </div>
              {selectedAccession && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => fetchProteinDetail(selectedAccession, true)}
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
                  <Skeleton className="h-7 w-36" />
                  <Skeleton className="h-4 w-64" />
                </div>
                <Skeleton className="h-8 w-24" />
              </div>
              <Skeleton className="h-28 w-full" />
              <div className="grid grid-cols-3 gap-4">
                <Skeleton className="h-20 w-full" />
                <Skeleton className="h-20 w-full" />
                <Skeleton className="h-20 w-full" />
              </div>
            </Card>
          ) : proteinDetail ? (
            <Card className="border-border/80 shadow-xs">
              {/* Record Top Bar */}
              <CardHeader className="p-5 border-b border-border/60">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono text-xs px-2 py-0.5 rounded bg-primary/10 text-primary font-bold">
                        {proteinDetail.accession}
                      </span>
                      {proteinDetail.gene_name && (
                        <Badge variant="outline" className="text-xs border-primary/30 text-primary">
                          Gene: {proteinDetail.gene_name}
                        </Badge>
                      )}
                      <Badge variant="secondary" className="text-xs">
                        {proteinDetail.organism}
                      </Badge>
                      {proteinDetail.entry_name && (
                        <span className="font-mono text-[11px] text-muted-foreground">
                          ({proteinDetail.entry_name})
                        </span>
                      )}
                    </div>
                    <h2 className="text-xl font-bold text-foreground tracking-tight">
                      {proteinDetail.protein_name}
                    </h2>
                  </div>

                  <div className="flex items-center gap-2">
                    <Badge
                      variant={proteinDetail.cached ? "outline" : "default"}
                      className={`text-[10px] gap-1 ${
                        proteinDetail.cached
                          ? "border-emerald-500/30 text-emerald-600 dark:text-emerald-400 bg-emerald-500/10"
                          : "bg-blue-600 text-white"
                      }`}
                    >
                      <Database className="h-3 w-3" />
                      <span>{proteinDetail.cached ? "PostgreSQL Cache" : "Live UniProtKB"}</span>
                    </Badge>

                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => fetchProteinDetail(proteinDetail.accession, true)}
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
                {/* Multi-Tab Workspace */}
                <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                  <TabsList className="grid w-full grid-cols-3 h-9">
                    <TabsTrigger value="overview" className="text-xs">
                      Overview & Function
                    </TabsTrigger>
                    <TabsTrigger value="sequence" className="text-xs">
                      Sequence & Properties
                    </TabsTrigger>
                    <TabsTrigger value="structures" className="text-xs">
                      3D Structures ({proteinDetail.pdb_structures_count} PDB)
                    </TabsTrigger>
                  </TabsList>

                  {/* TAB 1: OVERVIEW & FUNCTION */}
                  <TabsContent value="overview" className="space-y-5 pt-4">
                    {/* Functional Summary */}
                    <div className="space-y-2">
                      <div className="flex items-center gap-1.5 text-xs font-semibold text-foreground">
                        <FileText className="h-3.5 w-3.5 text-primary" />
                        <span>Biological Function</span>
                      </div>
                      {proteinDetail.function_summary ? (
                        <div className="rounded-lg bg-muted/40 border border-border/60 p-3.5 text-xs leading-relaxed text-muted-foreground">
                          {proteinDetail.function_summary}
                        </div>
                      ) : (
                        <p className="text-xs italic text-muted-foreground">
                          No curated functional narrative cataloged in UniProtKB.
                        </p>
                      )}
                    </div>

                    {/* Quick Metric Tiles */}
                    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                      <div className="rounded-lg border border-border/80 bg-card p-3">
                        <span className="text-[10px] uppercase font-semibold text-muted-foreground">Sequence Length</span>
                        <p className="mt-1 text-sm font-mono font-bold text-foreground">
                          {proteinDetail.sequence_length.toLocaleString()} aa
                        </p>
                      </div>

                      <div className="rounded-lg border border-border/80 bg-card p-3">
                        <span className="text-[10px] uppercase font-semibold text-muted-foreground">UniProt Mass</span>
                        <p className="mt-1 text-sm font-mono font-bold text-foreground">
                          {proteinDetail.mass_da ? `${proteinDetail.mass_da.toLocaleString()} Da` : "—"}
                        </p>
                      </div>

                      <div className="rounded-lg border border-border/80 bg-card p-3">
                        <span className="text-[10px] uppercase font-semibold text-muted-foreground">PDB Structures</span>
                        <p className="mt-1 text-sm font-mono font-bold text-foreground">
                          {proteinDetail.pdb_structures_count} models
                        </p>
                      </div>

                      <div className="rounded-lg border border-border/80 bg-card p-3">
                        <span className="text-[10px] uppercase font-semibold text-muted-foreground">AlphaFold Model</span>
                        <p className="mt-1 text-sm font-mono font-bold text-foreground">
                          {proteinDetail.has_alphafold ? "Available" : "Not cataloged"}
                        </p>
                      </div>
                    </div>

                    {/* Cellular Localization & Existence */}
                    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                      {proteinDetail.subcellular_location && (
                        <div className="rounded-lg border border-border/80 bg-card p-3 space-y-1">
                          <span className="text-[10px] uppercase font-semibold text-muted-foreground">Subcellular Location</span>
                          <p className="text-xs font-medium text-foreground">
                            {proteinDetail.subcellular_location}
                          </p>
                        </div>
                      )}

                      {proteinDetail.protein_existence && (
                        <div className="rounded-lg border border-border/80 bg-card p-3 space-y-1">
                          <span className="text-[10px] uppercase font-semibold text-muted-foreground">Evidence Level</span>
                          <p className="text-xs font-medium text-foreground">
                            {proteinDetail.protein_existence}
                          </p>
                        </div>
                      )}
                    </div>

                    {/* Post-Translational Modifications (PTMs) */}
                    {proteinDetail.ptms && proteinDetail.ptms.length > 0 && (
                      <div className="space-y-2">
                        <span className="text-xs font-semibold text-foreground">Curated Post-Translational Modifications (PTMs)</span>
                        <div className="flex flex-wrap gap-1.5">
                          {proteinDetail.ptms.map((ptm, idx) => (
                            <span
                              key={idx}
                              className="rounded-md border border-border/80 bg-muted/40 px-2.5 py-1 text-[11px] text-muted-foreground"
                            >
                              {ptm}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Cross-Database References */}
                    <div className="space-y-2 pt-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1.5 text-xs font-semibold text-foreground">
                          <Globe className="h-3.5 w-3.5 text-primary" />
                          <span>Cross-Database External Links</span>
                        </div>
                        <span className="text-[11px] text-muted-foreground">
                          {proteinDetail.references.length} direct links
                        </span>
                      </div>

                      <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
                        {proteinDetail.references.map((ref) => (
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
                  </TabsContent>

                  {/* TAB 2: SEQUENCE & PHYSICOCHEMICAL PROPERTIES */}
                  <TabsContent value="sequence" className="space-y-5 pt-4">
                    {sequenceLoading ? (
                      <div className="space-y-4">
                        <Skeleton className="h-28 w-full" />
                        <Skeleton className="h-36 w-full" />
                      </div>
                    ) : sequenceData ? (
                      <div className="space-y-5">
                        {/* Calculated Physicochemical Metrics Grid */}
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-1.5 text-xs font-semibold text-foreground">
                              <Sparkles className="h-3.5 w-3.5 text-primary" />
                              <span>Calculated Physicochemical Estimations (Biopython)</span>
                            </div>
                            <Badge variant="outline" className="text-[10px] border-primary/30 text-primary">
                              In Silico Analysis
                            </Badge>
                          </div>

                          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                            <div className="rounded-lg border border-border/80 bg-card p-3">
                              <span className="text-[10px] uppercase font-semibold text-muted-foreground">Theoretical Mass</span>
                              <p className="mt-1 text-sm font-mono font-bold text-foreground">
                                {sequenceData.properties.theoretical_molecular_weight_da
                                  ? `${sequenceData.properties.theoretical_molecular_weight_da.toLocaleString()} Da`
                                  : "—"}
                              </p>
                              <span className="text-[10px] text-muted-foreground">
                                {sequenceData.properties.theoretical_molecular_weight_da
                                  ? `(~${(sequenceData.properties.theoretical_molecular_weight_da / 1000).toFixed(2)} kDa)`
                                  : "Ambiguous residue"}
                              </span>
                            </div>

                            <div className="rounded-lg border border-border/80 bg-card p-3">
                              <span className="text-[10px] uppercase font-semibold text-muted-foreground">Isoelectric Point (pI)</span>
                              <p className="mt-1 text-sm font-mono font-bold text-foreground">
                                {sequenceData.properties.isoelectric_point ?? "—"}
                              </p>
                              <span className="text-[10px] text-muted-foreground">Bjellqvist pKa scale</span>
                            </div>

                            <div className="rounded-lg border border-border/80 bg-card p-3">
                              <span className="text-[10px] uppercase font-semibold text-muted-foreground">Charge at pH 7.0</span>
                              <p className="mt-1 text-sm font-mono font-bold text-foreground">
                                {sequenceData.properties.charge_at_ph7 !== null
                                  ? `${sequenceData.properties.charge_at_ph7 > 0 ? "+" : ""}${sequenceData.properties.charge_at_ph7}`
                                  : "—"}
                              </p>
                              <span className="text-[10px] text-muted-foreground">Net formal charge</span>
                            </div>

                            <div className="rounded-lg border border-border/80 bg-card p-3">
                              <span className="text-[10px] uppercase font-semibold text-muted-foreground">Instability Index</span>
                              <p className="mt-1 text-sm font-mono font-bold text-foreground">
                                {sequenceData.properties.instability_index ?? "—"}
                              </p>
                              <span className="text-[10px] text-muted-foreground">
                                {sequenceData.properties.is_stable === true
                                  ? "Predicted Stable (< 40)"
                                  : sequenceData.properties.is_stable === false
                                  ? "Predicted Unstable (>= 40)"
                                  : "—"}
                              </span>
                            </div>

                            <div className="rounded-lg border border-border/80 bg-card p-3">
                              <span className="text-[10px] uppercase font-semibold text-muted-foreground">GRAVY Hydropathy</span>
                              <p className="mt-1 text-sm font-mono font-bold text-foreground">
                                {sequenceData.properties.gravy_score ?? "—"}
                              </p>
                              <span className="text-[10px] text-muted-foreground">
                                {sequenceData.properties.gravy_score !== null
                                  ? sequenceData.properties.gravy_score > 0
                                    ? "Hydrophobic character"
                                    : "Hydrophilic character"
                                  : "—"}
                              </span>
                            </div>

                            <div className="rounded-lg border border-border/80 bg-card p-3">
                              <span className="text-[10px] uppercase font-semibold text-muted-foreground">Aromaticity</span>
                              <p className="mt-1 text-sm font-mono font-bold text-foreground">
                                {sequenceData.properties.aromaticity !== null
                                  ? `${(sequenceData.properties.aromaticity * 100).toFixed(1)}%`
                                  : "—"}
                              </p>
                              <span className="text-[10px] text-muted-foreground">Phe, Tyr, Trp fraction</span>
                            </div>
                          </div>
                        </div>

                        {/* Sequence Viewer & FASTA Export */}
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-semibold text-foreground">
                              Amino Acid Sequence ({sequenceData.length} aa)
                            </span>
                            <div className="flex items-center gap-2">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleCopy(sequenceData.sequence, "seq")}
                                className="h-7 text-[11px] gap-1"
                              >
                                {copiedKey === "seq" ? (
                                  <>
                                    <Check className="h-3 w-3 text-emerald-500" />
                                    <span>Copied!</span>
                                  </>
                                ) : (
                                  <>
                                    <Copy className="h-3 w-3" />
                                    <span>Copy Raw</span>
                                  </>
                                )}
                              </Button>

                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleDownloadFasta(sequenceData.fasta, sequenceData.accession)}
                                className="h-7 text-[11px] gap-1"
                              >
                                <Download className="h-3 w-3" />
                                <span>Export FASTA</span>
                              </Button>
                            </div>
                          </div>

                          <div className="rounded-lg border border-border bg-muted/30 p-3 font-mono text-xs text-foreground leading-relaxed break-all max-h-56 overflow-y-auto select-all">
                            {sequenceData.sequence}
                          </div>
                        </div>

                        {/* Scientific Methodology Caveat */}
                        <div className="rounded-lg border border-border/80 bg-muted/20 p-3 text-[11px] text-muted-foreground space-y-1">
                          <span className="font-semibold text-foreground">Computational Assumptions & Caveats:</span>
                          <ul className="list-disc pl-4 space-y-0.5">
                            {sequenceData.properties.computational_notes.map((note, i) => (
                              <li key={i}>{note}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    ) : (
                      <p className="text-xs italic text-muted-foreground">
                        Sequence data could not be computed for this record.
                      </p>
                    )}
                  </TabsContent>

                  {/* TAB 3: 3D STRUCTURES (RCSB PDB & ALPHAFOLD) */}
                  <TabsContent value="structures" className="space-y-6 pt-4">
                    {structuresLoading ? (
                      <div className="space-y-4">
                        <Skeleton className="h-28 w-full" />
                        <Skeleton className="h-44 w-full" />
                      </div>
                    ) : structuresData ? (
                      <div className="space-y-6">
                        {/* 1. AlphaFold AI Predicted Structure Card */}
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-1.5 text-xs font-semibold text-foreground">
                              <Box className="h-3.5 w-3.5 text-primary" />
                              <span>AlphaFold Computational AI Prediction</span>
                            </div>
                            <Badge variant="outline" className="text-[10px] border-blue-500/30 text-blue-600 dark:text-blue-400 bg-blue-500/10">
                              In Silico Model
                            </Badge>
                          </div>

                          {structuresData.predicted_structure ? (
                            <div className="rounded-lg border border-border/80 bg-card p-4 space-y-3">
                              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                                <div className="space-y-0.5">
                                  <div className="flex items-center gap-2">
                                    <span className="font-mono font-bold text-sm text-foreground">
                                      {structuresData.predicted_structure.entry_id}
                                    </span>
                                    {structuresData.predicted_structure.confidence_category && (
                                      <Badge variant="secondary" className="text-[10px]">
                                        {structuresData.predicted_structure.confidence_category}
                                      </Badge>
                                    )}
                                  </div>
                                  <p className="text-xs text-muted-foreground">
                                    Global pLDDT Confidence:{" "}
                                    <span className="font-mono font-semibold text-foreground">
                                      {structuresData.predicted_structure.global_plddt?.toFixed(1) ?? "—"} / 100
                                    </span>
                                  </p>
                                </div>

                                <div className="flex items-center gap-2">
                                  {structuresData.predicted_structure.pdb_url && (
                                    <a
                                      href={structuresData.predicted_structure.pdb_url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
                                    >
                                      <Download className="h-3 w-3" />
                                      <span>Download PDB</span>
                                    </a>
                                  )}
                                  <a
                                    href={structuresData.predicted_structure.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
                                  >
                                    <ExternalLink className="h-3 w-3" />
                                    <span>AlphaFold DB</span>
                                  </a>
                                </div>
                              </div>

                              <div className="rounded bg-muted/40 p-2.5 text-[11px] text-muted-foreground border border-border/60">
                                <strong>Scientific Disclaimer:</strong>{" "}
                                {structuresData.predicted_structure.prediction_note}
                              </div>
                            </div>
                          ) : (
                            <p className="text-xs italic text-muted-foreground">
                              No AlphaFold DB structure model currently cataloged for accession {proteinDetail.accession}.
                            </p>
                          )}
                        </div>

                        {/* 2. Experimentally Determined Structures (RCSB PDB) */}
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-1.5 text-xs font-semibold text-foreground">
                              <ShieldCheck className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
                              <span>Experimentally Determined Atomic Structures (RCSB PDB)</span>
                            </div>
                            <span className="text-[11px] text-muted-foreground">
                              {structuresData.experimental_count} experimental structures
                            </span>
                          </div>

                          {structuresData.experimental_structures.length > 0 ? (
                            <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 max-h-72 overflow-y-auto">
                              {structuresData.experimental_structures.map((pdb) => (
                                <a
                                  key={pdb.pdb_id}
                                  href={pdb.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="group flex items-start justify-between rounded-lg border border-border/80 bg-card p-3 hover:border-emerald-500/40 hover:bg-emerald-500/5 transition-all"
                                >
                                  <div className="space-y-1">
                                    <div className="flex items-center gap-2">
                                      <span className="font-mono font-bold text-sm text-foreground group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
                                        PDB {pdb.pdb_id}
                                      </span>
                                      <Badge variant="outline" className="text-[10px] py-0 px-1 border-border">
                                        {pdb.method}
                                      </Badge>
                                    </div>
                                    <div className="text-[11px] text-muted-foreground font-mono space-x-2">
                                      {pdb.resolution_angstrom && (
                                        <span>Resolution: {pdb.resolution_angstrom} Å</span>
                                      )}
                                      {pdb.chains && <span>Chains: {pdb.chains}</span>}
                                    </div>
                                  </div>
                                  <ExternalLink className="h-3.5 w-3.5 text-muted-foreground group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors shrink-0 mt-0.5" />
                                </a>
                              ))}
                            </div>
                          ) : (
                            <p className="text-xs italic text-muted-foreground">
                              No experimental PDB structures mapped to this UniProt entry yet.
                            </p>
                          )}
                        </div>
                      </div>
                    ) : (
                      <p className="text-xs italic text-muted-foreground">
                        Structural data could not be retrieved.
                      </p>
                    )}
                  </TabsContent>
                </Tabs>

                {/* Provenance Footer */}
                <div className="pt-3 border-t border-border/60 flex flex-wrap items-center justify-between gap-2 text-[11px] text-muted-foreground">
                  <span>Data Source: {proteinDetail.source}</span>
                  <span>Retrieved: {new Date(proteinDetail.retrieved_at).toLocaleString()}</span>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card className="border-border/80 p-12 text-center text-muted-foreground shadow-xs">
              <Activity className="h-10 w-10 mx-auto text-muted-foreground/40 mb-3" />
              <h3 className="text-sm font-semibold text-foreground">No Protein Selected</h3>
              <p className="mt-1 text-xs text-muted-foreground max-w-sm mx-auto">
                Search by keyword or select an accession from the search results on the left to explore its complete molecular and structural profile.
              </p>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ProteinIntelligencePage() {
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
      <ProteinIntelligenceContent />
    </Suspense>
  );
}

