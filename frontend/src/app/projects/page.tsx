"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  FolderKanban,
  Plus,
  Trash2,
  Tag,
  ArrowRight,
  Lock,
  Layers,
  Calendar,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { apiRequest } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

interface ProjectSummary {
  id: number;
  user_id: number;
  name: string;
  description: string | null;
  status: string;
  tags: string[] | null;
  items_count: number;
  created_at: string;
  updated_at: string;
}

export default function ProjectsPage() {
  const { user, token } = useAuth();
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New project dialog state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [newTags, setNewTags] = useState("");
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    async function fetchProjects() {
      if (!token) {
        setIsLoading(false);
        return;
      }
      setIsLoading(true);
      setError(null);
      try {
        const data = await apiRequest<ProjectSummary[]>("/api/v1/projects");
        setProjects(data);
      } catch (err: unknown) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError("Failed to load projects.");
        }
      } finally {
        setIsLoading(false);
      }
    }

    fetchProjects();
  }, [token]);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    setIsCreating(true);
    try {
      const tagsArray = newTags
        .split(",")
        .map((t) => t.trim())
        .filter((t) => t.length > 0);

      const created = await apiRequest<ProjectSummary>("/api/v1/projects", {
        method: "POST",
        body: {
          name: newTitle.trim(),
          description: newDescription.trim() || undefined,
          tags: tagsArray,
        },
      });

      setProjects([created, ...projects]);
      setNewTitle("");
      setNewDescription("");
      setNewTags("");
      setDialogOpen(false);
    } catch (err: unknown) {
      if (err instanceof Error) {
        alert(`Failed to create project: ${err.message}`);
      }
    } finally {
      setIsCreating(false);
    }
  };

  const handleDeleteProject = async (projectId: number, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this research project and all associated items?")) {
      return;
    }

    try {
      await apiRequest(`/api/v1/projects/${projectId}`, { method: "DELETE" });
      setProjects(projects.filter((p) => p.id !== projectId));
    } catch (err: unknown) {
      if (err instanceof Error) {
        alert(`Deletion error: ${err.message}`);
      }
    }
  };

  if (!user && !isLoading) {
    return (
      <div className="flex min-h-[70vh] flex-col items-center justify-center p-6 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-primary mb-4">
          <Lock className="h-7 w-7" />
        </div>
        <h2 className="text-xl font-bold tracking-tight text-foreground">
          Sign In to Access Research Projects
        </h2>
        <p className="mt-2 max-w-md text-xs text-muted-foreground leading-relaxed">
          Create projects to organize genomic loci, UniProt proteins, binding assays, and sequence laboratory analyses into dedicated, persistent workspaces.
        </p>
        <div className="mt-5 flex gap-3">
          <Link href="/login">
            <Button size="sm" className="h-9 text-xs font-semibold">
              Sign In
            </Button>
          </Link>
          <Link href="/register">
            <Button size="sm" variant="outline" className="h-9 text-xs font-semibold">
              Create Free Account
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6 md:p-8">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="border-primary/30 text-primary text-[10px]">
              <FolderKanban className="mr-1 h-3 w-3" />
              Workspaces
            </Badge>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-foreground">
            Research Projects
          </h1>
          <p className="text-xs text-muted-foreground">
            Manage your multi-omics target collections, experimental notes, and dossiers
          </p>
        </div>

        <Button size="sm" onClick={() => setDialogOpen(true)} className="h-9 text-xs gap-1.5 font-semibold">
          <Plus className="h-4 w-4" />
          <span>New Research Project</span>
        </Button>

        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent className="sm:max-w-md">
            <form onSubmit={handleCreateProject}>
              <DialogHeader>
                <DialogTitle className="text-base font-bold">Initialize Research Project</DialogTitle>
                <DialogDescription className="text-xs">
                  Create a dedicated workspace to save genes, proteins, diseases, and sequence records.
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-3.5 py-4">
                <div className="space-y-1">
                  <Label htmlFor="proj-name" className="text-xs font-medium">
                    Project Name *
                  </Label>
                  <Input
                    id="proj-name"
                    required
                    placeholder="e.g. EGFR Kinase Inhibitor Screening"
                    className="text-xs"
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                  />
                </div>

                <div className="space-y-1">
                  <Label htmlFor="proj-desc" className="text-xs font-medium">
                    Research Objective / Description
                  </Label>
                  <Input
                    id="proj-desc"
                    placeholder="Investigating mutant conformations and small-molecule binding..."
                    className="text-xs"
                    value={newDescription}
                    onChange={(e) => setNewDescription(e.target.value)}
                  />
                </div>

                <div className="space-y-1">
                  <Label htmlFor="proj-tags" className="text-xs font-medium">
                    Keywords / Tags (comma separated)
                  </Label>
                  <Input
                    id="proj-tags"
                    placeholder="Oncology, Kinase, Small Molecule, PDB"
                    className="text-xs"
                    value={newTags}
                    onChange={(e) => setNewTags(e.target.value)}
                  />
                </div>
              </div>

              <DialogFooter>
                <Button type="button" variant="ghost" size="sm" onClick={() => setDialogOpen(false)} className="text-xs">
                  Cancel
                </Button>
                <Button type="submit" size="sm" className="text-xs font-semibold" disabled={isCreating || !newTitle.trim()}>
                  {isCreating ? "Creating..." : "Initialize Workspace"}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse h-48 border-border/60 bg-card/40" />
          ))}
        </div>
      ) : error ? (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-xs text-destructive">
          {error}
        </div>
      ) : projects.length === 0 ? (
        <Card className="border-dashed border-border/80 bg-muted/20 p-12 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <FolderKanban className="h-6 w-6" />
          </div>
          <h3 className="mt-3 text-sm font-semibold text-foreground">No Research Projects Yet</h3>
          <p className="mt-1 max-w-sm text-xs text-muted-foreground mx-auto">
            Get started by initializing your first multi-omics investigation workspace.
          </p>
          <Button
            size="sm"
            onClick={() => setDialogOpen(true)}
            className="mt-4 text-xs font-semibold gap-1.5"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Create First Project</span>
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <Link key={project.id} href={`/projects/${project.id}`} className="group">
              <Card className="h-full border-border/80 transition-all duration-200 hover:border-primary/50 hover:shadow-xs flex flex-col justify-between">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <Badge
                      variant="outline"
                      className="text-[10px] uppercase font-bold tracking-wider capitalize"
                    >
                      {project.status}
                    </Badge>
                    <div className="flex items-center gap-1 text-[11px] text-muted-foreground">
                      <Layers className="h-3 w-3" />
                      <span>{project.items_count} items</span>
                    </div>
                  </div>
                  <CardTitle className="text-base font-bold text-foreground group-hover:text-primary transition-colors mt-2">
                    {project.name}
                  </CardTitle>
                  <CardDescription className="text-xs line-clamp-2">
                    {project.description || "No description provided."}
                  </CardDescription>
                </CardHeader>

                <CardContent className="pb-3">
                  {project.tags && project.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {project.tags.map((tag) => (
                        <span
                          key={tag}
                          className="inline-flex items-center gap-1 rounded bg-muted/60 px-1.5 py-0.5 text-[10px] text-muted-foreground"
                        >
                          <Tag className="h-2.5 w-2.5" />
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </CardContent>

                <CardFooter className="pt-2 border-t border-border/60 flex items-center justify-between text-xs text-muted-foreground">
                  <span className="text-[11px] flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {new Date(project.created_at).toLocaleDateString()}
                  </span>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={(e) => handleDeleteProject(project.id, e)}
                      title="Delete Project"
                      className="h-7 w-7 text-muted-foreground hover:text-destructive"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                    <ArrowRight className="h-4 w-4 text-primary transition-transform group-hover:translate-x-0.5" />
                  </div>
                </CardFooter>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
