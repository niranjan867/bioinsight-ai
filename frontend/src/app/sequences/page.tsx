"use client";

import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { AlertCircle, ArrowDownToLine, Dna, FlaskConical, LoaderCircle, Search, Upload } from "lucide-react";
import { ApiError, NetworkError, apiRequest } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type Kind = "dna" | "rna" | "protein";
type AnalysisRecord = {
  id: string; description: string; sequence_type: Kind; input_sequence: string; normalized_sequence: string;
  normalization: string; length: number; composition: Record<string, number>; percentages: Record<string, number>;
  gc_percent: number | null; at_percent: number | null; complement: string | null; reverse_complement: string | null;
  transcription: string | null; dinucleotide_frequency: Record<string, number>; codon_frequency: Record<string, number>;
  protein_properties: Record<string, number | null>; warnings: string[];
};
type Analysis = { records: AnalysisRecord[]; source: string; method: string };
type Translation = { translations: Record<string, string>; warnings: string[]; genetic_code: number };
type Alignment = { aligned_a: string; markers: string; aligned_b: string; score: number; identity_percent: number; alignment_length: number; mode: string };
type BlastJob = { job_id: string; status: string; message: string; results: Array<Record<string, unknown>> | null };

const EXAMPLE = ">example DNA sequence\nATGGCCATTGTAATGGGCCGCTGAAAGGGTGCCCGATAG";
const ALIGNMENT_EXAMPLE = "ATGGCCATTGTAATGGGCCGCTGAAAGGGTGCCCGATAT";

function saveFile(name: string, content: string, type: string) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name;
  anchor.click();
  URL.revokeObjectURL(url);
}

export default function SequenceLaboratoryPage() {
  const [sequence, setSequence] = useState(EXAMPLE);
  const [sequenceB, setSequenceB] = useState(ALIGNMENT_EXAMPLE);
  const [kind, setKind] = useState<Kind>("dna");
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [translation, setTranslation] = useState<Translation | null>(null);
  const [alignment, setAlignment] = useState<Alignment | null>(null);
  const [blast, setBlast] = useState<BlastJob | null>(null);
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function run(action: "analyze" | "translate" | "align" | "blast") {
    setLoading(action);
    setError(null);
    try {
      const body = { sequence, sequence_type: kind, genetic_code: 1 };
      if (action === "analyze") setAnalysis(await apiRequest<Analysis>("/api/v1/sequences/analyze", { method: "POST", body }));
      if (action === "translate") {
        if (kind === "protein") throw new Error("Translation requires DNA or RNA input.");
        setTranslation(await apiRequest<Translation>("/api/v1/sequences/translate?frame=six", { method: "POST", body }));
      }
      if (action === "align") {
        const clean = sequence.split("\n").filter((line) => !line.startsWith(">" )).join("");
        setAlignment(await apiRequest<Alignment>("/api/v1/sequences/align", { method: "POST", body: { sequence_a: clean, sequence_b: sequenceB, mode: "global" } }));
      }
      if (action === "blast") {
        if (kind === "rna") throw new Error("Choose DNA or protein for NCBI BLAST.");
        const job = await apiRequest<BlastJob>("/api/v1/sequences/blast", { method: "POST", body: { sequence, sequence_type: kind, database: kind === "protein" ? "nr" : "nt" } });
        setBlast(job);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : err instanceof NetworkError ? err.message : err instanceof Error ? err.message : "Sequence operation failed.");
    } finally {
      setLoading(null);
    }
  }

  useEffect(() => {
    if (!blast || blast.status !== "running") return;
    const timer = window.setTimeout(async () => {
      try {
        setBlast(await apiRequest<BlastJob>(`/api/v1/sequences/blast/${blast.job_id}`));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not poll the BLAST job.");
      }
    }, 5000);
    return () => window.clearTimeout(timer);
  }, [blast]);

  async function upload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setLoading("upload"); setError(null);
    const form = new FormData(); form.set("file", file);
    try {
      setAnalysis(await apiRequest<Analysis>("/api/v1/sequences/upload", { method: "POST", params: { sequence_type: kind }, body: form }));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : err instanceof NetworkError ? err.message : "FASTA upload failed.");
    } finally { setLoading(null); event.target.value = ""; }
  }

  function submit(event: FormEvent) { event.preventDefault(); void run("analyze"); }

  return (
    <main className="space-y-6 p-6 md:p-8">
      <section className="rounded-xl border bg-gradient-to-r from-card to-primary/5 p-6 md:p-8">
        <div className="flex flex-wrap items-center gap-2"><Badge variant="outline"><FlaskConical className="mr-1 h-3 w-3" />Sequence Laboratory</Badge><span className="text-xs text-muted-foreground">Biopython • NCBI BLAST</span></div>
        <h1 className="mt-3 text-2xl font-bold md:text-3xl">Sequence analysis</h1>
        <p className="mt-2 max-w-3xl text-sm text-muted-foreground">Analyze DNA, RNA, and protein sequences, translate reading frames, compare sequences, and submit NCBI BLAST jobs. Ambiguous IUPAC symbols are retained where supported.</p>
      </section>

      <Card>
        <CardHeader><CardTitle>Sequence input</CardTitle><CardDescription>Paste a raw sequence or multi-record FASTA. Whitespace is ignored for analysis; the response retains the submitted text.</CardDescription></CardHeader>
        <CardContent>
          <form onSubmit={submit} className="space-y-4">
            <div className="flex flex-wrap items-center gap-3">
              <label className="text-sm font-medium" htmlFor="sequence-kind">Sequence type</label>
              <select id="sequence-kind" value={kind} onChange={(event) => setKind(event.target.value as Kind)} className="h-9 rounded-md border bg-background px-3 text-sm">
                <option value="dna">DNA</option><option value="rna">RNA</option><option value="protein">Protein</option>
              </select>
              <label className="inline-flex cursor-pointer items-center gap-2 rounded-md border px-3 py-2 text-sm hover:bg-muted"><Upload className="h-4 w-4" />Upload FASTA<input className="sr-only" type="file" accept=".fa,.fasta,.fna,.faa,.txt" onChange={upload} /></label>
            </div>
            <textarea aria-label="Sequence input" value={sequence} onChange={(event) => setSequence(event.target.value)} rows={9} spellCheck={false} className="w-full resize-y rounded-md border bg-background p-3 font-mono text-xs leading-relaxed" />
            <div><label htmlFor="alignment-sequence" className="mb-1 block text-sm font-medium">Second sequence for pairwise alignment</label><textarea id="alignment-sequence" value={sequenceB} onChange={(event) => setSequenceB(event.target.value)} rows={3} spellCheck={false} className="w-full resize-y rounded-md border bg-background p-3 font-mono text-xs leading-relaxed" /></div>
            <div className="flex flex-wrap gap-2">
              <Button type="submit" disabled={loading !== null}><Dna className="mr-2 h-4 w-4" />{loading === "analyze" ? "Analyzing…" : "Analyze sequence"}</Button>
              <Button type="button" variant="outline" disabled={loading !== null || kind === "protein"} onClick={() => void run("translate")}>{loading === "translate" && <LoaderCircle className="mr-2 h-4 w-4 animate-spin" />}Translate six frames</Button>
              <Button type="button" variant="outline" disabled={loading !== null} onClick={() => void run("align")}>Align input</Button>
              <Button type="button" variant="outline" disabled={loading !== null || kind === "rna"} onClick={() => void run("blast")}><Search className="mr-2 h-4 w-4" />Submit BLAST</Button>
            </div>
          </form>
          {error && <div role="alert" className="mt-4 flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive"><AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />{error}</div>}
        </CardContent>
      </Card>

      {analysis && <Card><CardHeader className="flex flex-row items-start justify-between"><div><CardTitle>Analysis results</CardTitle><CardDescription>{analysis.source} • {analysis.method}</CardDescription></div><Button size="sm" variant="outline" onClick={() => saveFile("sequence-analysis.json", JSON.stringify(analysis, null, 2), "application/json")}><ArrowDownToLine className="mr-2 h-4 w-4" />Export JSON</Button></CardHeader><CardContent className="space-y-5">
        {analysis.records.map((record) => <section key={record.id} className="space-y-3 border-t pt-4 first:border-0 first:pt-0"><h2 className="font-semibold">{record.description || record.id}<span className="ml-2 text-xs font-normal text-muted-foreground">{record.sequence_type.toUpperCase()}</span></h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4"><Metric label="Length" value={`${record.length.toLocaleString()} nt / aa`} />{record.gc_percent !== null && <Metric label="GC" value={`${record.gc_percent}%`} />} {record.at_percent !== null && <Metric label="AT / AU" value={`${record.at_percent}%`} />}{Object.entries(record.protein_properties).filter(([, value]) => value !== null).map(([name, value]) => <Metric key={name} label={name.replaceAll("_", " ")} value={String(value)} />)}</div>
          <div className="grid gap-4 md:grid-cols-2"><div><p className="mb-1 text-xs font-semibold uppercase text-muted-foreground">Composition</p><p className="font-mono text-sm">{Object.entries(record.composition).map(([symbol, count]) => `${symbol}: ${count} (${record.percentages[symbol]}%)`).join(" · ")}</p></div>{record.reverse_complement && <div><p className="mb-1 text-xs font-semibold uppercase text-muted-foreground">Reverse complement</p><pre className="overflow-auto rounded bg-muted p-2 font-mono text-xs">{record.reverse_complement}</pre></div>}</div>
          {record.warnings.length > 0 && <ul className="list-inside list-disc text-xs text-amber-700">{record.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>}
        </section>)}
      </CardContent></Card>}

      {translation && <Card><CardHeader><CardTitle>Six-frame translation</CardTitle><CardDescription>Genetic code {translation.genetic_code}; stop codons are shown as *.</CardDescription></CardHeader><CardContent className="space-y-3">{Object.entries(translation.translations).map(([frame, value]) => <div key={frame}><p className="mb-1 text-xs font-semibold">Frame {frame}</p><pre className="overflow-auto rounded bg-muted p-2 font-mono text-xs">{value}</pre></div>)}</CardContent></Card>}

      {alignment && <Card><CardHeader><CardTitle>Pairwise alignment</CardTitle><CardDescription>{alignment.mode} • score {alignment.score} • {alignment.identity_percent}% identity • {alignment.alignment_length} positions</CardDescription></CardHeader><CardContent><pre className="overflow-auto rounded bg-muted p-3 font-mono text-xs">{alignment.aligned_a}{"\n"}{alignment.markers}{"\n"}{alignment.aligned_b}</pre></CardContent></Card>}

      {blast && <Card><CardHeader><CardTitle>NCBI BLAST job</CardTitle><CardDescription>{blast.status}: {blast.message}</CardDescription></CardHeader><CardContent>{blast.status === "running" && <p className="text-sm text-muted-foreground">Polling NCBI every five seconds. Jobs are held in this backend process and are lost if it restarts.</p>}{blast.results && blast.results.length > 0 ? <div className="overflow-auto"><table className="w-full text-left text-xs"><thead><tr className="border-b"><th className="p-2">Subject</th><th className="p-2">Identity</th><th className="p-2">E-value</th><th className="p-2">Query coverage</th></tr></thead><tbody>{blast.results.map((hit, index) => <tr key={`${String(hit.subject_id)}-${index}`} className="border-b"><td className="p-2">{String(hit.subject_title)}</td><td className="p-2">{String(hit.identity_percent)}%</td><td className="p-2">{String(hit.e_value)}</td><td className="p-2">{String(hit.query_coverage_percent)}%</td></tr>)}</tbody></table><Button className="mt-3" size="sm" variant="outline" onClick={() => saveFile("blast-results.json", JSON.stringify(blast.results, null, 2), "application/json")}>Download results</Button></div> : blast.status === "completed" ? <p className="text-sm text-muted-foreground">NCBI returned no alignments for this query.</p> : null}</CardContent></Card>}
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="rounded-lg border p-3"><p className="text-xs capitalize text-muted-foreground">{label}</p><p className="mt-1 break-words font-mono text-sm font-semibold">{value}</p></div>;
}
