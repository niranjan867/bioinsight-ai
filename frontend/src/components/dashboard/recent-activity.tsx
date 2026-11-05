"use client";

import Link from "next/link";
import { History, Sparkles } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export function RecentActivity() {
  return (
    <Card className="border-border/80 bg-card shadow-xs">
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <div>
          <CardTitle className="text-base font-semibold">Recent Activity</CardTitle>
          <CardDescription className="text-xs">
            Audit log of sequence analyses, structural queries, and pipeline executions
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        {/* Clearly labeled empty state (no fake activity) */}
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border/80 bg-muted/20 py-8 px-4 text-center">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary">
            <History className="h-5 w-5" />
          </div>
          <h3 className="mt-3 text-xs font-semibold text-foreground">
            No Recent Activity
          </h3>
          <p className="mt-1 max-w-sm text-[11px] text-muted-foreground leading-relaxed">
            Your laboratory executions, BLAST searches, and multi-omics queries will automatically be logged here once initiated.
          </p>
          <div className="mt-4 flex gap-2">
            <Link href="/sequences">
              <Button size="sm" variant="outline" className="h-8 text-xs gap-1.5">
                <Sparkles className="h-3.5 w-3.5 text-primary" />
                <span>Launch Sequence Lab</span>
              </Button>
            </Link>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

