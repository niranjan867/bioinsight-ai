"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  FileText,
  FileDown,
  FolderKanban,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { apiRequest, getApiBaseUrl } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

interface ProjectSummary {
  id: number;
  name: string;
  description: string | null;
  items_count: number;
  status: string;
}

export default function ReportsPage() {
  const { user, token } = useAuth();
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [isLoadingProjects, setIsLoadingProjects] = useState(false);

  // Custom report form state
  const [customTitle, setCustomTitle] = useState("Genomic Target Screening Report");
  const [customSubtitle, setCustomSubtitle] = useState("Multi-Omics Comparative Characterization");
  const [customSummary, setCustomSummary] = useState(
    "This report provides systematic investigation metrics for candidate biological targets. All records are cross-referenced with MyGene.info, UniProtKB, and PDB."
  );
  const [customSectionTitle, setCustomSectionTitle] = useState("Key Biological Targets");
  const [customSectionContent, setCustomSectionContent] = useState(
    "Target 1: BRCA1 (Human DNA Repair, Chr 17)\nTarget 2: TP53 (Cellular Tumor Suppressor, Chr 17)\nTarget 3: EGFR (Receptor Tyrosine Kinase, Chr 7)"
  );

  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    async function fetchProjects() {
      if (!token) return;
      setIsLoadingProjects(true);
      try {
        const data = await apiRequest<ProjectSummary[]>("/api/v1/projects");
        setProjects(data);
        if (data.length > 0) {
          setSelectedProjectId(data[0].id);
        }
      } catch {
        setProjects([]);
      } finally {
        setIsLoadingProjects(false);
      }
    }

    fetchProjects();
  }, [token]);

  const handleDownloadProjectReport = async (format: "pdf" | "docx") => {
    if (!selectedProjectId || !token) {
      alert("Please select a valid research project.");
      return;
    }
    setIsGenerating(true);
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/api/v1/reports/project/${selectedProjectId}/${format}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`Report generation failed with HTTP ${res.status}`);

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `project_${selectedProjectId}_report.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: unknown) {
      if (err instanceof Error) alert(err.message);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownloadCustomReport = async (format: "pdf" | "docx") => {
    if (!customTitle.trim()) {
      alert("Please provide a report title.");
      return;
    }
    setIsGenerating(true);
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/api/v1/reports/${format}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          title: customTitle.trim(),
          subtitle: customSubtitle.trim() || undefined,
          author_name: user?.full_name || "BioInsight AI Researcher",
          summary: customSummary.trim(),
          sections: [
            {
              title: customSectionTitle.trim(),
              content: customSectionContent.trim(),
            },
          ],
          references: [
            "MyGene.info / NCBI Entrez Gene",
            "UniProt Knowledgebase (UniProtKB)",
            "RCSB Protein Data Bank",
            "BioInsight AI Computational Biology Platform",
          ],
        }),
      });

      if (!res.ok) throw new Error(`Report generation failed with HTTP ${res.status}`);

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${customTitle.toLowerCase().replace(/\s+/g, "_")}.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: unknown) {
      if (err instanceof Error) alert(err.message);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="space-y-6 p-6 md:p-8 max-w-5xl mx-auto">
      {/* Title */}
      <div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="border-primary/30 text-primary text-[10px]">
            <FileText className="mr-1 h-3 w-3" />
            Publication & Export
          </Badge>
          <span className="text-xs text-muted-foreground">PDF & DOCX Generator</span>
        </div>
        <h1 className="mt-1 text-2xl font-bold tracking-tight text-foreground">
          Scientific Research Reports
        </h1>
        <p className="text-xs text-muted-foreground">
          Generate publication-grade PDF and editable Microsoft Word (DOCX) dossiers containing your curated biological targets and experimental findings
        </p>
      </div>

      <Tabs defaultValue="project" className="space-y-4">
        <TabsList className="bg-muted/60 p-1">
          <TabsTrigger value="project" className="text-xs gap-1.5">
            <FolderKanban className="h-3.5 w-3.5" />
            <span>Export Project Dossier</span>
          </TabsTrigger>
          <TabsTrigger value="custom" className="text-xs gap-1.5">
            <FileText className="h-3.5 w-3.5" />
            <span>Custom Report Studio</span>
          </TabsTrigger>
        </TabsList>

        {/* Tab 1: Export Project Dossier */}
        <TabsContent value="project">
          <Card className="border-border/80 bg-card shadow-xs">
            <CardHeader>
              <CardTitle className="text-base font-bold">Export Research Project Dossier</CardTitle>
              <CardDescription className="text-xs">
                Compile all saved genes, proteins, compounds, binding assays, and activity audit trails into an official document
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {!user ? (
                <div className="rounded-lg border border-dashed border-border/80 bg-muted/20 p-8 text-center text-xs text-muted-foreground">
                  <p>Please sign in to select and export your saved research projects.</p>
                  <Link href="/login" className="mt-2 inline-block">
                    <Button size="sm" className="text-xs font-semibold">Sign In</Button>
                  </Link>
                </div>
              ) : isLoadingProjects ? (
                <p className="text-xs text-muted-foreground">Loading projects...</p>
              ) : projects.length === 0 ? (
                <div className="rounded-lg border border-dashed border-border/80 bg-muted/20 p-8 text-center text-xs text-muted-foreground">
                  <p>You have no active projects yet.</p>
                  <Link href="/projects" className="mt-2 inline-block">
                    <Button size="sm" className="text-xs font-semibold">Create Project</Button>
                  </Link>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="space-y-1">
                    <Label className="text-xs font-medium">Select Research Project</Label>
                    <select
                      className="w-full rounded-md border border-input bg-background p-2.5 text-xs"
                      value={selectedProjectId || ""}
                      onChange={(e) => setSelectedProjectId(Number(e.target.value))}
                    >
                      {projects.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name} ({p.items_count} items, status: {p.status})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="flex flex-wrap items-center gap-3 pt-2">
                    <Button
                      size="sm"
                      onClick={() => handleDownloadProjectReport("pdf")}
                      disabled={isGenerating || !selectedProjectId}
                      className="text-xs font-semibold gap-1.5 h-9"
                    >
                      <FileDown className="h-4 w-4" />
                      <span>{isGenerating ? "Compiling..." : "Export as PDF Report"}</span>
                    </Button>

                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDownloadProjectReport("docx")}
                      disabled={isGenerating || !selectedProjectId}
                      className="text-xs font-semibold gap-1.5 h-9"
                    >
                      <FileText className="h-4 w-4 text-blue-600" />
                      <span>{isGenerating ? "Compiling..." : "Export as Word (DOCX)"}</span>
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 2: Custom Report Studio */}
        <TabsContent value="custom">
          <Card className="border-border/80 bg-card shadow-xs">
            <CardHeader>
              <CardTitle className="text-base font-bold">Custom Report Studio</CardTitle>
              <CardDescription className="text-xs">
                Draft a custom scientific report with structured sections, executive summary, and citations
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <Label className="text-xs font-medium">Report Title *</Label>
                  <Input
                    className="text-xs"
                    value={customTitle}
                    onChange={(e) => setCustomTitle(e.target.value)}
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs font-medium">Subtitle / Scope</Label>
                  <Input
                    className="text-xs"
                    value={customSubtitle}
                    onChange={(e) => setCustomSubtitle(e.target.value)}
                  />
                </div>
              </div>

              <div className="space-y-1">
                <Label className="text-xs font-medium">Executive Scientific Summary</Label>
                <textarea
                  rows={3}
                  className="w-full rounded-md border border-input bg-background p-2.5 text-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  value={customSummary}
                  onChange={(e) => setCustomSummary(e.target.value)}
                />
              </div>

              <div className="space-y-1">
                <Label className="text-xs font-medium">Section Headline</Label>
                <Input
                  className="text-xs"
                  value={customSectionTitle}
                  onChange={(e) => setCustomSectionTitle(e.target.value)}
                />
              </div>

              <div className="space-y-1">
                <Label className="text-xs font-medium">Section Content</Label>
                <textarea
                  rows={4}
                  className="w-full rounded-md border border-input bg-background p-2.5 text-xs font-mono text-[11px] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  value={customSectionContent}
                  onChange={(e) => setCustomSectionContent(e.target.value)}
                />
              </div>

              <div className="flex flex-wrap items-center gap-3 pt-2">
                <Button
                  size="sm"
                  onClick={() => handleDownloadCustomReport("pdf")}
                  disabled={isGenerating || !customTitle.trim()}
                  className="text-xs font-semibold gap-1.5 h-9"
                >
                  <FileDown className="h-4 w-4" />
                  <span>Generate PDF Document</span>
                </Button>

                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleDownloadCustomReport("docx")}
                  disabled={isGenerating || !customTitle.trim()}
                  className="text-xs font-semibold gap-1.5 h-9"
                >
                  <FileText className="h-4 w-4 text-blue-600" />
                  <span>Generate Word (DOCX)</span>
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
