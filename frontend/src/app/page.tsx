import Link from "next/link";
import {
  Dna,
  FlaskConical,
  Sparkles,
  Server,
  ArrowUpRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { SystemStatusCard } from "@/components/dashboard/system-status";
import { QuickAccessGrid } from "@/components/dashboard/quick-access-grid";
import { ProjectsOverview } from "@/components/dashboard/projects-overview";
import { RecentActivity } from "@/components/dashboard/recent-activity";
import { QuickTools } from "@/components/dashboard/quick-tools";

export default function HomePage() {
  return (
    <div className="space-y-6 p-6 md:p-8">
      {/* 1. Welcome Section */}
      <div className="relative overflow-hidden rounded-xl border border-border/80 bg-gradient-to-r from-card via-card to-primary/5 p-6 md:p-8 shadow-xs">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="max-w-2xl space-y-2">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="gap-1 border-primary/30 text-primary text-[11px]">
                <Sparkles className="h-3 w-3" />
                <span>Next-Gen Multi-Omics</span>
              </Badge>
              <span className="text-xs text-muted-foreground">Version 0.1.0</span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground md:text-3xl">
              BioInsight AI Research Platform
            </h1>
            <p className="text-sm leading-relaxed text-muted-foreground">
              A high-precision computational biology suite designed for researchers and life scientists.
              Investigate genomic architecture, explore proteomic pathways, run sequence transformations,
              and correlate molecular phenotypes in a unified local research environment.
            </p>
          </div>

          <div className="flex flex-wrap gap-2.5">
            <Link href="/sequences">
              <Button size="sm" className="h-9 gap-1.5 text-xs font-semibold">
                <FlaskConical className="h-4 w-4" />
                <span>Sequence Laboratory</span>
              </Button>
            </Link>
            <Link href="/genes">
              <Button size="sm" variant="outline" className="h-9 gap-1.5 text-xs font-semibold">
                <Dna className="h-4 w-4 text-primary" />
                <span>Explore Genes</span>
              </Button>
            </Link>
            <Link href="/api-test">
              <Button size="sm" variant="ghost" className="h-9 gap-1.5 text-xs text-muted-foreground hover:text-foreground">
                <Server className="h-3.5 w-3.5" />
                <span>Diagnostics</span>
                <ArrowUpRight className="h-3 w-3" />
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* 2. System Status Live Connectivity Tile */}
      <SystemStatusCard />

      {/* 3. Quick Access Intelligence Modules */}
      <QuickAccessGrid />

      {/* 4. Two-Column Layout: Projects & Recent Activity */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <ProjectsOverview />
        <RecentActivity />
      </div>

      {/* 5. In-Browser Scientific Quick Tools */}
      <QuickTools />
    </div>
  );
}
