"use client";

import Link from "next/link";
import { Plus, FolderPlus } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export function ProjectsOverview() {
  return (
    <Card className="border-border/80 bg-card shadow-xs">
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <div>
          <CardTitle className="text-base font-semibold">Research Projects</CardTitle>
          <CardDescription className="text-xs">
            Organized multi-omics investigations and datasets
          </CardDescription>
        </div>
        <Link href="/projects">
          <Button size="sm" variant="outline" className="h-8 text-xs gap-1.5">
            <Plus className="h-3.5 w-3.5" />
            <span>New Project</span>
          </Button>
        </Link>
      </CardHeader>
      <CardContent>
        {/* Clearly labeled empty state (no fake statistics) */}
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border/80 bg-muted/20 py-8 px-4 text-center">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary">
            <FolderPlus className="h-5 w-5" />
          </div>
          <h3 className="mt-3 text-xs font-semibold text-foreground">
            No Active Projects
          </h3>
          <p className="mt-1 max-w-sm text-[11px] text-muted-foreground leading-relaxed">
            Create a project to bundle gene targets, sequence assays, and structural models into a collaborative workspace.
          </p>
          <Link href="/projects" className="mt-4">
            <Button size="sm" variant="default" className="h-8 text-xs">
              Initialize First Project
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}

