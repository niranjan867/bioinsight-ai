"use client";

import React, { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  FileDown,
  Plus,
  Trash2,
  Calendar,
  Layers,
  ArrowLeft,
  Dna,
  Activity,
  Atom,
  HeartPulse,
  FlaskConical,
  StickyNote,
  Clock,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiRequest, getApiBaseUrl } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

interface ProjectItem {
  id: number;
  project_id: number;
  item_type: string;
  item_id: string;
  title: string;
  description: string | null;
  metadata_json: Record<string, unknown> | null;
  created_at: string;
}

interface ProjectActivity {
  id: number;
  project_id: number;
  user_id: number;
  action: string;
  details: Record<string, unknown> | null;
  created_at: string;
}

interface ProjectDetail {
  id: number;
  user_id: number;
  name: string;
  description: string | null;
  status: string;
  tags: string[] | null;
  items_count: number;
  items: ProjectItem[];
  activities: ProjectActivity[];
  created_at: string;
  updated_at: string;
}

function ProjectDetailContent() {
  const params = useParams();
  const { token } = useAuth();
  const projectId = params?.id as string;

  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Note dialog
  const [noteOpen, setNoteOpen] = useState(false);
  const [noteTitle, setNoteTitle] = useState("");
  const [noteText, setNoteText] = useState("");
  const [isSavingNote, setIsSavingNote] = useState(false);

  useEffect(() => {
    async function loadProject() {
      if (!projectId || !token) {
        setIsLoading(false);
        return;
      }
      setIsLoading(true);
      setError(null);
      try {
        const data = await apiRequest<ProjectDetail>(`/api/v1/projects/${projectId}`);
        setProject(data);
      } catch (err: unknown) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError("Failed to load project details.");
        }
      } finally {
        setIsLoading(false);
      }
    }

    loadProject();
  }, [projectId, token]);

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!noteTitle.trim() || !project) return;

    setIsSavingNote(true);
    try {
      const newItem = await apiRequest<ProjectItem>(`/api/v1/projects/${project.id}/items`, {
        method: "POST",
        body: {
          item_type: "note",
          item_id: `NOTE-${Date.now()}`,
          title: noteTitle.trim(),
          description: noteText.trim() || undefined,
        },
      });

      setProject({
        ...project,
        items: [newItem, ...project.items],
        items_count: project.items_count + 1,
      });

      setNoteTitle("");
      setNoteText("");
      setNoteOpen(false);
    } catch (err: unknown) {
      if (err instanceof Error) {
        alert(`Failed to add note: ${err.message}`);
      }
    } finally {
      setIsSavingNote(false);
    }
  };

  const handleDeleteItem = async (itemId: number) => {
    if (!project) return;
    try {
      await apiRequest(`/api/v1/projects/${project.id}/items/${itemId}`, {
        method: "DELETE",
      });
      setProject({
        ...project,
        items: project.items.filter((i) => i.id !== itemId),
        items_count: Math.max(0, project.items_count - 1),
      });
    } catch (err: unknown) {
      if (err instanceof Error) {
        alert(`Failed to remove item: ${err.message}`);
      }
    }
  };

  const handleDownloadReport = async (format: "pdf" | "docx") => {
    if (!project || !token) return;
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/api/v1/reports/project/${project.id}/${format}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`Report export failed with HTTP ${res.status}`);

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `project_${project.id}_${project.name.toLowerCase().replace(/\s+/g, "_")}.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: unknown) {
      if (err instanceof Error) {
        alert(err.message);
      }
    }
  };

  const getItemIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case "gene":
        return <Dna className="h-4 w-4 text-blue-500" />;
      case "protein":
        return <Activity className="h-4 w-4 text-teal-500" />;
      case "compound":
        return <Atom className="h-4 w-4 text-emerald-500" />;
      case "disease":
        return <HeartPulse className="h-4 w-4 text-rose-500" />;
      case "sequence":
        return <FlaskConical className="h-4 w-4 text-indigo-500" />;
      default:
        return <StickyNote className="h-4 w-4 text-amber-500" />;
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6 p-6 md:p-8 animate-pulse">
        <div className="h-8 w-48 bg-muted rounded" />
        <div className="h-32 bg-card rounded-xl" />
        <div className="h-64 bg-card rounded-xl" />
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="p-8 text-center space-y-4">
        <p className="text-sm text-destructive">{error || "Project not found."}</p>
        <Link href="/projects">
          <Button size="sm" variant="outline" className="text-xs gap-1.5">
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Back to Projects</span>
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6 md:p-8">
      {/* Back button & Action Bar */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <Link href="/projects">
            <Button size="icon" variant="outline" className="h-8 w-8">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-[10px] uppercase font-bold tracking-wider capitalize">
                {project.status}
              </Badge>
              <span className="text-xs text-muted-foreground flex items-center gap-1">
                <Calendar className="h-3 w-3" />
                Created {new Date(project.created_at).toLocaleDateString()}
              </span>
            </div>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-foreground">
              {project.name}
            </h1>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Add Note Button */}
          <Button
            size="sm"
            variant="outline"
            onClick={() => setNoteOpen(true)}
            className="h-8 text-xs gap-1.5 font-medium"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Add Note</span>
          </Button>

          <Dialog open={noteOpen} onOpenChange={setNoteOpen}>
            <DialogContent className="sm:max-w-md">
              <form onSubmit={handleAddNote}>
                <DialogHeader>
                  <DialogTitle className="text-base font-bold">Add Research Note</DialogTitle>
                  <DialogDescription className="text-xs">
                    Record observations, hypotheses, or protocol details for this investigation.
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-3 py-4">
                  <div className="space-y-1">
                    <Label htmlFor="note-title" className="text-xs font-medium">
                      Note Title *
                    </Label>
                    <Input
                      id="note-title"
                      required
                      placeholder="e.g. Binding pocket mutation hypothesis"
                      className="text-xs"
                      value={noteTitle}
                      onChange={(e) => setNoteTitle(e.target.value)}
                    />
                  </div>
                  <div className="space-y-1">
                    <Label htmlFor="note-content" className="text-xs font-medium">
                      Note Content
                    </Label>
                    <textarea
                      id="note-content"
                      rows={4}
                      placeholder="Observed hydrogen bonding shift around residue Tyr419..."
                      className="w-full rounded-md border border-input bg-background p-2.5 text-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                      value={noteText}
                      onChange={(e) => setNoteText(e.target.value)}
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button type="button" variant="ghost" size="sm" onClick={() => setNoteOpen(false)} className="text-xs">
                    Cancel
                  </Button>
                  <Button type="submit" size="sm" className="text-xs font-semibold" disabled={isSavingNote || !noteTitle.trim()}>
                    {isSavingNote ? "Saving..." : "Save Note"}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>

          {/* Export PDF */}
          <Button
            size="sm"
            variant="outline"
            onClick={() => handleDownloadReport("pdf")}
            className="h-8 text-xs gap-1.5 font-medium"
          >
            <FileDown className="h-3.5 w-3.5 text-primary" />
            <span>Export PDF</span>
          </Button>

          {/* Export DOCX */}
          <Button
            size="sm"
            variant="outline"
            onClick={() => handleDownloadReport("docx")}
            className="h-8 text-xs gap-1.5 font-medium"
          >
            <FileDown className="h-3.5 w-3.5 text-blue-600" />
            <span>Export DOCX</span>
          </Button>
        </div>
      </div>

      {/* Description & Metadata Card */}
      <Card className="border-border/80 bg-card shadow-xs">
        <CardContent className="pt-5 space-y-3">
          <p className="text-xs text-muted-foreground leading-relaxed">
            {project.description || "No objective description provided for this project."}
          </p>
          {project.tags && project.tags.length > 0 && (
            <div className="flex flex-wrap gap-1.5 pt-1">
              {project.tags.map((tag) => (
                <Badge key={tag} variant="secondary" className="text-[10px] font-medium">
                  {tag}
                </Badge>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Main Tabs: Saved Entities vs Timeline */}
      <Tabs defaultValue="items" className="space-y-4">
        <TabsList className="bg-muted/60 p-1">
          <TabsTrigger value="items" className="text-xs gap-1.5">
            <Layers className="h-3.5 w-3.5" />
            <span>Saved Targets & Items ({project.items.length})</span>
          </TabsTrigger>
          <TabsTrigger value="timeline" className="text-xs gap-1.5">
            <Clock className="h-3.5 w-3.5" />
            <span>Investigation Timeline ({project.activities.length})</span>
          </TabsTrigger>
        </TabsList>

        {/* Tab 1: Saved Items */}
        <TabsContent value="items" className="space-y-4">
          {project.items.length === 0 ? (
            <Card className="border-dashed border-border/80 bg-muted/20 p-10 text-center">
              <Layers className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
              <h3 className="text-xs font-semibold text-foreground">No Items in This Workspace</h3>
              <p className="text-[11px] text-muted-foreground mt-1 max-w-sm mx-auto">
                Save genes from Gene Intelligence, proteins from Protein Intelligence, compounds from Chem, or add custom laboratory notes.
              </p>
            </Card>
          ) : (
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              {project.items.map((item) => (
                <Card key={item.id} className="border-border/80 bg-card shadow-xs flex flex-col justify-between">
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {getItemIcon(item.item_type)}
                        <Badge variant="outline" className="text-[10px] uppercase font-bold tracking-wider">
                          {item.item_type}
                        </Badge>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDeleteItem(item.id)}
                        title="Remove from project"
                        className="h-6 w-6 text-muted-foreground hover:text-destructive"
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                    <CardTitle className="text-sm font-bold text-foreground mt-1">
                      {item.title}
                    </CardTitle>
                    <CardDescription className="text-[11px] font-mono text-primary">
                      ID: {item.item_id}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="pb-3 text-xs text-muted-foreground leading-relaxed">
                    {item.description || "Target entity recorded in this research workspace."}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Tab 2: Activity Timeline */}
        <TabsContent value="timeline">
          <Card className="border-border/80 bg-card">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold">Audit & Timeline Log</CardTitle>
              <CardDescription className="text-xs">
                Historical record of actions performed in this project
              </CardDescription>
            </CardHeader>
            <CardContent>
              {project.activities.length === 0 ? (
                <p className="text-xs text-muted-foreground">No activity recorded yet.</p>
              ) : (
                <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-border">
                  {project.activities.map((act) => (
                    <div key={act.id} className="relative">
                      <span className="absolute -left-6 top-1 h-2.5 w-2.5 rounded-full bg-primary border-2 border-background" />
                      <div className="flex items-baseline justify-between text-xs">
                        <span className="font-semibold text-foreground capitalize">
                          {act.action.replace(/_/g, " ")}
                        </span>
                        <span className="text-[10px] text-muted-foreground">
                          {new Date(act.created_at).toLocaleString()}
                        </span>
                      </div>
                      {act.details && (
                        <p className="text-[11px] text-muted-foreground mt-0.5">
                          {JSON.stringify(act.details)}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default function ProjectDetailPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-sm text-muted-foreground">Loading project...</div>}>
      <ProjectDetailContent />
    </Suspense>
  );
}
