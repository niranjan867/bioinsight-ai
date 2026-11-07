"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus, FolderPlus, ArrowRight, Layers } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { apiRequest } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

interface ProjectItem {
  id: number;
  name: string;
  description: string | null;
  items_count: number;
  status: string;
}

export function ProjectsOverview() {
  const { user, token } = useAuth();
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    async function fetchUserProjects() {
      if (!token) return;
      setIsLoading(true);
      try {
        const data = await apiRequest<ProjectItem[]>("/api/v1/projects");
        setProjects(data.slice(0, 3));
      } catch {
        setProjects([]);
      } finally {
        setIsLoading(false);
      }
    }

    fetchUserProjects();
  }, [token]);

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
        {isLoading ? (
          <div className="py-6 text-center text-xs text-muted-foreground">Loading projects...</div>
        ) : projects.length > 0 ? (
          <div className="space-y-2.5">
            {projects.map((proj) => (
              <Link
                key={proj.id}
                href={`/projects/${proj.id}`}
                className="group flex items-center justify-between rounded-lg border border-border/80 p-3 hover:border-primary/50 hover:bg-muted/30 transition-all text-xs"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-foreground group-hover:text-primary transition-colors">
                      {proj.name}
                    </span>
                    <Badge variant="outline" className="text-[9px] uppercase">
                      {proj.status}
                    </Badge>
                  </div>
                  <p className="text-[11px] text-muted-foreground line-clamp-1">
                    {proj.description || "Research workspace dataset."}
                  </p>
                </div>
                <div className="flex items-center gap-2 text-muted-foreground shrink-0">
                  <span className="text-[10px] flex items-center gap-1">
                    <Layers className="h-3 w-3" />
                    {proj.items_count} items
                  </span>
                  <ArrowRight className="h-3.5 w-3.5 text-primary group-hover:translate-x-0.5 transition-transform" />
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border/80 bg-muted/20 py-8 px-4 text-center">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary">
              <FolderPlus className="h-5 w-5" />
            </div>
            <h3 className="mt-3 text-xs font-semibold text-foreground">
              {user ? "No Active Projects" : "Sign In to View Projects"}
            </h3>
            <p className="mt-1 max-w-sm text-[11px] text-muted-foreground leading-relaxed">
              Create a project to bundle gene targets, sequence assays, and structural models into a collaborative workspace.
            </p>
            <Link href={user ? "/projects" : "/login"} className="mt-4">
              <Button size="sm" variant="default" className="h-8 text-xs">
                {user ? "Initialize First Project" : "Sign In to Workspace"}
              </Button>
            </Link>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
