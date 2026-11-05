"use client";

import { useState } from "react";
import { Wrench, Check, Copy, ArrowRightLeft } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function QuickTools() {
  const [sequence, setSequence] = useState("ATGCGATCGATCGATCGATC");
  const [copied, setCopied] = useState(false);

  // Simple client-side sequence statistics
  const cleanSeq = sequence.toUpperCase().replace(/[^ATCGU]/g, "");
  const length = cleanSeq.length;
  const gcCount = (cleanSeq.match(/[GC]/g) || []).length;
  const gcPercent = length > 0 ? ((gcCount / length) * 100).toFixed(1) : "0.0";

  // Reverse complement calculation
  const complementMap: Record<string, string> = {
    A: "T",
    T: "A",
    C: "G",
    G: "C",
    U: "A",
  };
  const reverseComplement = cleanSeq
    .split("")
    .reverse()
    .map((base) => complementMap[base] || base)
    .join("");

  const handleCopy = () => {
    navigator.clipboard.writeText(reverseComplement);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Card className="border-border/80 bg-card shadow-xs">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <Wrench className="h-4 w-4 text-primary" />
              <span>Bioinformatics Utility Hub</span>
            </CardTitle>
            <CardDescription className="text-xs">
              Quick in-browser sequence calculations and transformations
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Interactive Mini-Tool: Quick GC% & Reverse Complement */}
        <div className="rounded-lg border border-border/70 bg-muted/20 p-3.5 space-y-3">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-foreground">Interactive Sequence Inspector</span>
            <span className="text-[10px] text-muted-foreground font-mono">IUPAC Nucleotides</span>
          </div>

          <div>
            <Input
              value={sequence}
              onChange={(e) => setSequence(e.target.value)}
              placeholder="Paste nucleotide sequence (A, T, C, G)..."
              className="font-mono text-xs uppercase bg-background h-8"
            />
          </div>

          {/* Metrics row */}
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 text-xs font-mono">
            <div className="rounded border border-border/60 bg-card p-2 text-center">
              <div className="text-[10px] text-muted-foreground uppercase">Length</div>
              <div className="mt-0.5 font-bold text-foreground">{length} bp</div>
            </div>
            <div className="rounded border border-border/60 bg-card p-2 text-center">
              <div className="text-[10px] text-muted-foreground uppercase">GC Content</div>
              <div className="mt-0.5 font-bold text-primary">{gcPercent}%</div>
            </div>
            <div className="rounded border border-border/60 bg-card p-2 text-center">
              <div className="text-[10px] text-muted-foreground uppercase">AT Content</div>
              <div className="mt-0.5 font-bold text-foreground">
                {length > 0 ? (100 - parseFloat(gcPercent)).toFixed(1) : "0.0"}%
              </div>
            </div>
            <div className="rounded border border-border/60 bg-card p-2 text-center">
              <div className="text-[10px] text-muted-foreground uppercase">GC Count</div>
              <div className="mt-0.5 font-bold text-foreground">{gcCount}</div>
            </div>
          </div>

          {/* Reverse Complement Output */}
          {reverseComplement && (
            <div className="flex items-center justify-between rounded border border-border/50 bg-background/80 px-2.5 py-1.5 text-xs font-mono">
              <div className="flex items-center gap-2 truncate pr-2">
                <ArrowRightLeft className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                <span className="truncate text-muted-foreground">
                  RevComp: <span className="text-foreground">{reverseComplement}</span>
                </span>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleCopy}
                className="h-6 w-6 shrink-0"
                aria-label="Copy reverse complement"
              >
                {copied ? <Check className="h-3.5 w-3.5 text-emerald-600" /> : <Copy className="h-3.5 w-3.5" />}
              </Button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

