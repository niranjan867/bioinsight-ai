"use client";

import React, { useState } from "react";
import {
  Bot,
  Send,
  ExternalLink,
  Copy,
  Check,
  BookOpen,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { apiRequest } from "@/lib/api";

let messageCounter = 0;
function getNextId(prefix: string): string {
  messageCounter += 1;
  return `${prefix}-${messageCounter}`;
}

function getFormattedTime(): string {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

interface CitationItem {
  source: string;
  identifier: string;
  title: string;
  url: string | null;
}

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: CitationItem[];
  source_modules?: string[];
  timestamp: string;
}

interface AssistantResponse {
  answer: string;
  citations: CitationItem[];
  confidence: number;
  source_modules: string[];
  engine: string;
}

export default function AssistantPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "initial",
      role: "assistant",
      content:
        "Welcome to the **BioInsight AI Grounded Research Assistant**. I am connected directly to your local bioinformatics database and official scientific APIs (MyGene.info, UniProtKB, Open Targets, PubChem, and Biopython). Ask any question regarding genomic loci, protein properties, chemical compounds, or disease associations.",
      timestamp: "Just now",
      source_modules: ["Bioinformatics Knowledgebase"],
    },
  ]);
  const [inputQuery, setInputQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const samplePrompts = [
    "What are the genomic coordinates and functional summary for human BRCA1?",
    "Compare molecular properties and Lipinski compliance of Aspirin vs Metformin",
    "What is the sequence length, mass, and subcellular location of human Hemoglobin Beta (P68871)?",
    "What are the top genetic targets associated with Asthma in Open Targets?",
    "Explain the function of TP53 and list its key biological roles",
  ];

  const handleSendMessage = async (textToSend: string) => {
    const q = textToSend.trim();
    if (!q || isLoading) return;

    const userMsg: ChatMessage = {
      id: getNextId("user"),
      role: "user",
      content: q,
      timestamp: getFormattedTime(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery("");
    setIsLoading(true);

    try {
      const res = await apiRequest<AssistantResponse>("/api/v1/assistant/chat", {
        method: "POST",
        body: { query: q },
      });

      const assistantMsg: ChatMessage = {
        id: getNextId("assistant"),
        role: "assistant",
        content: res.answer,
        citations: res.citations,
        source_modules: res.source_modules,
        timestamp: getFormattedTime(),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: unknown) {
      const errorMsg: ChatMessage = {
        id: getNextId("error"),
        role: "assistant",
        content:
          err instanceof Error
            ? `Query failed: ${err.message}`
            : "Assistant failed to generate response. Please verify backend connectivity.",
        timestamp: getFormattedTime(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 1500);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] p-4 md:p-6 space-y-4 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="border-primary/30 text-primary text-[10px]">
            <Bot className="mr-1 h-3 w-3" />
            Evidence-Grounded AI
          </Badge>
          <span className="text-xs text-muted-foreground">Deterministic Scientific Synthesis</span>
        </div>
        <h1 className="text-xl font-bold tracking-tight text-foreground">
          AI Research Assistant
        </h1>
        <p className="text-xs text-muted-foreground">
          Ask questions cross-referencing genomics, proteomics, disease genetics, and cheminformatics with real citations
        </p>
      </div>

      {/* Chat Messages Scroll Container */}
      <Card className="flex-1 flex flex-col overflow-hidden border-border/80 bg-card shadow-xs">
        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-5">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 text-xs leading-relaxed ${
                msg.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {msg.role === "assistant" && (
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-xs">
                  <Bot className="h-4 w-4" />
                </div>
              )}

              <div
                className={`max-w-[85%] rounded-xl p-4 space-y-2.5 ${
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground font-medium rounded-tr-none"
                    : "bg-muted/40 border border-border/70 text-foreground rounded-tl-none shadow-xs"
                }`}
              >
                {/* Content */}
                <div className="whitespace-pre-wrap leading-relaxed">
                  {msg.content}
                </div>

                {/* Citations & Source Modules (if assistant) */}
                {msg.role === "assistant" && msg.citations && msg.citations.length > 0 && (
                  <div className="pt-2 border-t border-border/60 space-y-1.5">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1">
                      <BookOpen className="h-3 w-3 text-primary" />
                      <span>Verified Evidence Citations:</span>
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {msg.citations.map((c, idx) => (
                        <a
                          key={idx}
                          href={c.url || "#"}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 rounded border border-border bg-background px-2 py-0.5 text-[10px] font-mono text-primary hover:bg-muted transition-colors"
                        >
                          <span className="font-semibold">{c.source}:</span>
                          <span>{c.identifier}</span>
                          {c.url && <ExternalLink className="h-2.5 w-2.5" />}
                        </a>
                      ))}
                    </div>
                  </div>
                )}

                {/* Footer Toolbar */}
                <div className="flex items-center justify-between text-[10px] text-muted-foreground pt-1">
                  <span>{msg.timestamp}</span>
                  {msg.role === "assistant" && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(msg.content, msg.id)}
                      className="h-5 px-1.5 text-[10px] text-muted-foreground hover:text-foreground gap-1"
                    >
                      {copiedId === msg.id ? (
                        <>
                          <Check className="h-2.5 w-2.5 text-emerald-600" />
                          <span>Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="h-2.5 w-2.5" />
                          <span>Copy</span>
                        </>
                      )}
                    </Button>
                  )}
                </div>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex gap-3 text-xs">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-xs animate-pulse">
                <Bot className="h-4 w-4" />
              </div>
              <div className="rounded-xl border border-border/70 bg-muted/30 p-3.5 text-xs text-muted-foreground space-y-1.5">
                <div className="flex items-center gap-2">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-primary" />
                  </span>
                  <span>Querying biological databases & synthesizing answer...</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Quick Suggestion Pills */}
        <div className="px-4 py-2 bg-muted/20 border-t border-border/60 flex items-center gap-1.5 overflow-x-auto scrollbar-none text-[11px]">
          <span className="text-muted-foreground shrink-0 text-[10px] font-semibold uppercase">Prompts:</span>
          {samplePrompts.map((prompt, i) => (
            <button
              key={i}
              type="button"
              onClick={() => handleSendMessage(prompt)}
              className="shrink-0 rounded-full border border-border bg-card px-2.5 py-0.5 text-foreground hover:border-primary/50 hover:bg-muted transition-colors truncate max-w-[260px]"
            >
              {prompt}
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <div className="p-3 bg-card border-t border-border/80">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage(inputQuery);
            }}
            className="flex gap-2"
          >
            <Input
              type="text"
              placeholder="Ask about genes, protein structures, chemical properties, or diseases..."
              className="text-xs h-10 bg-muted/20"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              disabled={isLoading}
            />
            <Button type="submit" size="sm" className="h-10 px-4 text-xs font-semibold gap-1.5" disabled={isLoading || !inputQuery.trim()}>
              <Send className="h-3.5 w-3.5" />
              <span>Send</span>
            </Button>
          </form>
        </div>
      </Card>
    </div>
  );
}
