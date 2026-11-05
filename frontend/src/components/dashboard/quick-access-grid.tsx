"use client";

import Link from "next/link";
import {
  Dna,
  Activity,
  FlaskConical,
  HeartPulse,
  Atom,
  ArrowRight,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface ModuleCard {
  title: string;
  category: string;
  description: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  tags: string[];
  colorClass: string;
}

const modules: ModuleCard[] = [
  {
    title: "Explore Genes",
    category: "Genomics",
    description:
      "Query genomic loci, gene architectures, transcript isoforms, and expression profiles across curated organisms.",
    href: "/genes",
    icon: Dna,
    tags: ["Ensembl", "NCBI", "Isoforms"],
    colorClass: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20",
  },
  {
    title: "Explore Proteins",
    category: "Proteomics",
    description:
      "Investigate polypeptide sequences, functional domains, post-translational modifications, and UniProt annotations.",
    href: "/proteins",
    icon: Activity,
    tags: ["UniProt", "Domains", "PTMs"],
    colorClass: "bg-teal-500/10 text-teal-600 dark:text-teal-400 border-teal-500/20",
  },
  {
    title: "Analyze Sequences",
    category: "Laboratory",
    description:
      "Execute pairwise alignments, GC content statistics, reverse complementation, and codon usage metrics.",
    href: "/sequences",
    icon: FlaskConical,
    tags: ["FASTA", "Alignment", "GC Content"],
    colorClass: "bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border-indigo-500/20",
  },
  {
    title: "Explore Diseases",
    category: "Clinical Genetics",
    description:
      "Map genetic etiologies, clinically significant pathogenic variants, and phenotypic disease associations.",
    href: "/diseases",
    icon: HeartPulse,
    tags: ["ClinVar", "GWAS", "Phenotypes"],
    colorClass: "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20",
  },
  {
    title: "Explore Compounds",
    category: "Cheminformatics",
    description:
      "Search bioactive small molecules, SMILES canonical representations, molecular weights, and binding targets.",
    href: "/compounds",
    icon: Atom,
    tags: ["PubChem", "ChEMBL", "SMILES"],
    colorClass: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20",
  },
];

export function QuickAccessGrid() {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold tracking-tight text-foreground">
            Research Intelligence Modules
          </h2>
          <p className="text-xs text-muted-foreground">
            Direct access to bioinformatics analytical engines
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {modules.map((mod) => {
          const Icon = mod.icon;
          return (
            <Link key={mod.title} href={mod.href} className="group">
              <Card className="h-full border-border/80 transition-all duration-200 hover:border-primary/50 hover:shadow-sm">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className={`flex h-9 w-9 items-center justify-center rounded-lg border ${mod.colorClass}`}>
                      <Icon className="h-5 w-5" />
                    </div>
                    <Badge variant="outline" className="text-[10px] font-normal text-muted-foreground border-border/70">
                      {mod.category}
                    </Badge>
                  </div>
                  <CardTitle className="mt-2 text-sm font-semibold group-hover:text-primary transition-colors flex items-center justify-between">
                    <span>{mod.title}</span>
                    <ArrowRight className="h-4 w-4 opacity-0 transition-all -translate-x-1 group-hover:opacity-100 group-hover:translate-x-0 text-primary" />
                  </CardTitle>
                  <CardDescription className="text-xs leading-relaxed line-clamp-2">
                    {mod.description}
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="flex flex-wrap gap-1.5 pt-2 border-t border-border/40">
                    {mod.tags.map((tag) => (
                      <span
                        key={tag}
                        className="rounded bg-muted/60 px-1.5 py-0.5 text-[10px] text-muted-foreground font-mono"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </Link>
          );
        })}
      </div>
    </div>
  );
}

