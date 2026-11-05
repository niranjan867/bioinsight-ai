"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiRequest } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Laptop,
  Server,
  Database,
  CheckCircle2,
  XCircle,
  RefreshCw,
  ExternalLink,
} from "lucide-react";

interface HealthData {
  backend: boolean;
  database: boolean;
  appName?: string;
  version?: string;
  lastChecked?: string;
}

export function SystemStatusCard() {
  const [status, setStatus] = useState<HealthData>({
    backend: false,
    database: false,
  });
  const [loading, setLoading] = useState(true);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  useEffect(() => {
    let ignore = false;

    async function loadHealth() {
      let backendOk = false;
      let dbOk = false;
      let appName: string | undefined;
      let version: string | undefined;

      try {
        const apiRes = await apiRequest<{
          status: string;
          application: string;
          version: string;
        }>("/api/v1/health");
        if (apiRes.status === "healthy") {
          backendOk = true;
          appName = apiRes.application;
          version = apiRes.version;
        }
      } catch {
        backendOk = false;
      }

      try {
        const dbRes = await apiRequest<{ status: string; database: string }>("/api/v1/health/db");
        if (dbRes.status === "healthy" && dbRes.database === "connected") {
          dbOk = true;
        }
      } catch {
        dbOk = false;
      }

      if (!ignore) {
        setStatus({
          backend: backendOk,
          database: dbOk,
          appName,
          version,
          lastChecked: new Date().toLocaleTimeString(),
        });
        setLoading(false);
      }
    }

    loadHealth();

    return () => {
      ignore = true;
    };
  }, [refreshTrigger]);

  const handleManualRefresh = () => {
    setLoading(true);
    setRefreshTrigger((prev) => prev + 1);
  };

  const allOperational = status.backend && status.database;

  return (
    <Card className="border-border/80 bg-card shadow-xs">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base font-semibold">System Connectivity</CardTitle>
            <CardDescription className="text-xs">
              Live status of computational nodes and database engine
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={handleManualRefresh}
              disabled={loading}
              className="h-8 w-8 text-muted-foreground hover:text-foreground"
              aria-label="Refresh status"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            </Button>
            <Badge
              variant={allOperational ? "default" : "destructive"}
              className={allOperational ? "bg-emerald-600 hover:bg-emerald-600 text-white" : ""}
            >
              {loading ? "Checking..." : allOperational ? "All Systems Operational" : "Service Disruption"}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          {/* Frontend Tile */}
          <div className="flex items-center justify-between rounded-lg border border-border/60 bg-muted/20 p-3">
            <div className="flex items-center gap-2.5">
              <div className="rounded-md bg-primary/10 p-2 text-primary">
                <Laptop className="h-4 w-4" />
              </div>
              <div>
                <div className="text-xs font-medium text-foreground">Next.js Client</div>
                <div className="text-[10px] text-muted-foreground">Port 3000</div>
              </div>
            </div>
            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
          </div>

          {/* Backend Tile */}
          <div className="flex items-center justify-between rounded-lg border border-border/60 bg-muted/20 p-3">
            <div className="flex items-center gap-2.5">
              <div className="rounded-md bg-primary/10 p-2 text-primary">
                <Server className="h-4 w-4" />
              </div>
              <div>
                <div className="text-xs font-medium text-foreground">FastAPI Engine</div>
                <div className="text-[10px] text-muted-foreground">
                  {status.version ? `v${status.version}` : "127.0.0.1:8000"}
                </div>
              </div>
            </div>
            {status.backend ? (
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
            ) : (
              <XCircle className="h-4 w-4 text-destructive" />
            )}
          </div>

          {/* Database Tile */}
          <div className="flex items-center justify-between rounded-lg border border-border/60 bg-muted/20 p-3">
            <div className="flex items-center gap-2.5">
              <div className="rounded-md bg-primary/10 p-2 text-primary">
                <Database className="h-4 w-4" />
              </div>
              <div>
                <div className="text-xs font-medium text-foreground">PostgreSQL 18</div>
                <div className="text-[10px] text-muted-foreground">bioinsight_db</div>
              </div>
            </div>
            {status.database ? (
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
            ) : (
              <XCircle className="h-4 w-4 text-destructive" />
            )}
          </div>
        </div>

        <div className="mt-3 flex items-center justify-between border-t border-border/50 pt-2 text-[11px] text-muted-foreground">
          <span>Last verification: {status.lastChecked ?? "Just now"}</span>
          <Link
            href="/api-test"
            className="flex items-center gap-1 text-primary hover:underline font-medium"
          >
            Detailed Diagnostics <ExternalLink className="h-3 w-3" />
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
