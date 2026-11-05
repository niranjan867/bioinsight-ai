"use client";

import { useEffect, useState } from "react";
import { apiRequest, ApiError, NetworkError, getApiBaseUrl } from "@/lib/api";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Activity,
  CheckCircle2,
  XCircle,
  Database,
  Server,
  RefreshCw,
  Clock,
  Laptop,
  AlertTriangle,
} from "lucide-react";

interface ApiHealthResponse {
  status: string;
  api_version: string;
  application: string;
  version: string;
}

interface DbHealthResponse {
  status: string;
  database: string;
}

export default function ApiTestPage() {
  const [loading, setLoading] = useState(true);
  const [refreshKey, setRefreshKey] = useState(0);
  const [lastChecked, setLastChecked] = useState<string | null>(null);
  const [lastSuccess, setLastSuccess] = useState<string | null>(null);

  // Backend state
  const [backendStatus, setBackendStatus] = useState<"healthy" | "error" | "loading">("loading");
  const [backendData, setBackendData] = useState<ApiHealthResponse | null>(null);
  const [backendError, setBackendError] = useState<string | null>(null);

  // Database state
  const [dbStatus, setDbStatus] = useState<"connected" | "error" | "loading">("loading");
  const [dbData, setDbData] = useState<DbHealthResponse | null>(null);
  const [dbError, setDbError] = useState<string | null>(null);

  useEffect(() => {
    let ignore = false;

    async function executeDiagnostics() {
      // 1. Fetch Backend Health
      try {
        const apiRes = await apiRequest<ApiHealthResponse>("/api/v1/health");
        if (!ignore) {
          setBackendData(apiRes);
          setBackendStatus("healthy");
          setBackendError(null);
        }
      } catch (err) {
        if (!ignore) {
          setBackendStatus("error");
          setBackendData(null);
          if (err instanceof ApiError) {
            setBackendError(`API Error (${err.status}): ${err.message}`);
          } else if (err instanceof NetworkError) {
            setBackendError(err.message);
          } else {
            setBackendError("Failed to connect to backend server");
          }
        }
      }

      // 2. Fetch Database Health
      try {
        const dbRes = await apiRequest<DbHealthResponse>("/api/v1/health/db");
        if (!ignore) {
          setDbData(dbRes);
          setDbStatus("connected");
          setDbError(null);
          setLastSuccess(new Date().toLocaleTimeString());
        }
      } catch (err) {
        if (!ignore) {
          setDbStatus("error");
          setDbData(null);
          if (err instanceof ApiError) {
            setDbError(`Database Unavailable (${err.status}): ${err.message}`);
          } else if (err instanceof NetworkError) {
            setDbError(err.message);
          } else {
            setDbError("Failed to verify database health");
          }
        }
      } finally {
        if (!ignore) {
          setLoading(false);
          setLastChecked(new Date().toLocaleTimeString());
        }
      }
    }

    executeDiagnostics();

    return () => {
      ignore = true;
    };
  }, [refreshKey]);

  const handleRefresh = () => {
    setLoading(true);
    setBackendError(null);
    setDbError(null);
    setRefreshKey((prev) => prev + 1);
  };

  const apiBaseUrl = getApiBaseUrl();

  return (
    <div className="p-6 md:p-8">
      <div className="mx-auto max-w-4xl space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-foreground">
              BioInsight AI Diagnostics
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Real-time verification of Frontend, FastAPI Backend, and PostgreSQL Database
            </p>
          </div>
          <Button
            onClick={handleRefresh}
            disabled={loading}
            className="w-fit"
            variant="default"
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Refresh Status
          </Button>
        </div>

        {/* Global Connectivity Banner */}
        <Card className="border-border">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-primary" />
                <CardTitle>System Connectivity Overview</CardTitle>
              </div>
              <Badge
                variant={
                  backendStatus === "healthy" && dbStatus === "connected"
                    ? "default"
                    : "destructive"
                }
              >
                {backendStatus === "healthy" && dbStatus === "connected"
                  ? "All Systems Operational"
                  : "Degraded or Disconnected"}
              </Badge>
            </div>
            <CardDescription>
              Backend Endpoint: <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">{apiBaseUrl}</code>
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap items-center gap-6 text-sm">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <span>Last Checked: {lastChecked ?? "Pending..."}</span>
            </div>
            {lastSuccess && (
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                <span>Last Verified: {lastSuccess}</span>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Status Component Cards */}
        <div className="grid gap-6 md:grid-cols-3">
          {/* Frontend Card */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Laptop className="h-5 w-5 text-primary" />
                  <CardTitle className="text-base">Frontend</CardTitle>
                </div>
                <Badge variant="default" className="bg-emerald-600 text-white">
                  Active
                </Badge>
              </div>
              <CardDescription>Next.js 16 Web Application</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Framework:</span>
                <span className="font-medium">Next.js 16.4 (App Router)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Language:</span>
                <span className="font-medium">TypeScript</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Host:</span>
                <span className="font-medium">localhost:3000</span>
              </div>
            </CardContent>
          </Card>

          {/* Backend Card */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Server className="h-5 w-5 text-primary" />
                  <CardTitle className="text-base">Backend API</CardTitle>
                </div>
                {backendStatus === "healthy" ? (
                  <Badge variant="default" className="bg-emerald-600 text-white">
                    Healthy
                  </Badge>
                ) : backendStatus === "loading" ? (
                  <Badge variant="secondary">Checking...</Badge>
                ) : (
                  <Badge variant="destructive">Failed</Badge>
                )}
              </div>
              <CardDescription>FastAPI Application Engine</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 text-xs">
              {backendData ? (
                <>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Application:</span>
                    <span className="font-medium">{backendData.application}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Version:</span>
                    <span className="font-medium">{backendData.version}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">API Scope:</span>
                    <span className="font-medium">{backendData.api_version}</span>
                  </div>
                </>
              ) : (
                <div className="rounded bg-destructive/10 p-2 text-destructive">
                  <div className="flex items-center gap-1 font-semibold">
                    <XCircle className="h-4 w-4" /> Connection Error
                  </div>
                  <p className="mt-1 break-words text-[11px]">{backendError ?? "Backend service unreachable"}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Database Card */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Database className="h-5 w-5 text-primary" />
                  <CardTitle className="text-base">Database</CardTitle>
                </div>
                {dbStatus === "connected" ? (
                  <Badge variant="default" className="bg-emerald-600 text-white">
                    Connected
                  </Badge>
                ) : dbStatus === "loading" ? (
                  <Badge variant="secondary">Checking...</Badge>
                ) : (
                  <Badge variant="destructive">Offline</Badge>
                )}
              </div>
              <CardDescription>PostgreSQL 18.6 Engine</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 text-xs">
              {dbData ? (
                <>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Database:</span>
                    <span className="font-medium">bioinsight_db</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">User:</span>
                    <span className="font-medium">bioinsight_app</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Dialect:</span>
                    <span className="font-medium">PostgreSQL (psycopg 3)</span>
                  </div>
                </>
              ) : (
                <div className="rounded bg-destructive/10 p-2 text-destructive">
                  <div className="flex items-center gap-1 font-semibold">
                    <AlertTriangle className="h-4 w-4" /> Query Failed
                  </div>
                  <p className="mt-1 break-words text-[11px]">{dbError ?? "Database check failed"}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Technical Diagnostics Details */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Diagnostic Endpoints</CardTitle>
            <CardDescription>
              Raw endpoint specifications and communication channels
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-xs font-mono">
            <div className="flex items-center justify-between border-b pb-2">
              <span className="text-muted-foreground">GET /api/v1/health</span>
              <span className="text-foreground">
                {backendData ? `Status: ${backendData.status}` : "Unreachable"}
              </span>
            </div>
            <div className="flex items-center justify-between border-b pb-2">
              <span className="text-muted-foreground">GET /api/v1/health/db (SELECT 1 query)</span>
              <span className="text-foreground">
                {dbData ? `Status: ${dbData.status}` : "Query Error"}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">CORS Allow Origin</span>
              <span className="text-foreground">http://localhost:3000</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
