/**
 * BioInsight AI - Core API Client
 * Robust, typed client for backend communication with error handling and request cancellation.
 */

export interface ApiRequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  params?: Record<string, string | number | boolean | undefined | null>;
  timeoutMs?: number;
}

export class ApiError extends Error {
  public readonly status: number;
  public readonly statusText: string;
  public readonly data: unknown;

  constructor(status: number, statusText: string, data?: unknown, message?: string) {
    super(message ?? `API Error ${status}: ${statusText}`);
    this.name = "ApiError";
    this.status = status;
    this.statusText = statusText;
    this.data = data;
  }
}

export class NetworkError extends Error {
  public readonly originalError?: unknown;

  constructor(message: string, originalError?: unknown) {
    super(message);
    this.name = "NetworkError";
    this.originalError = originalError;
  }
}

/**
 * Resolves the configured API base URL, defaulting to local FastAPI host.
 */
export function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
}

/**
 * Execute a typed API request to the BioInsight FastAPI backend.
 */
export async function apiRequest<T = unknown>(
  endpoint: string,
  options: ApiRequestOptions = {}
): Promise<T> {
  const {
    body,
    params,
    timeoutMs = 8000,
    headers: customHeaders,
    signal: userSignal,
    ...fetchOptions
  } = options;

  const baseUrl = getApiBaseUrl();
  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const url = new URL(`${baseUrl}${cleanEndpoint}`);

  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null) {
        url.searchParams.append(key, String(value));
      }
    }
  }

  // Handle timeout and cancellation
  const controller = new AbortController();
  const timeoutId = setTimeout(() => {
    controller.abort(new Error(`Request timed out after ${timeoutMs}ms`));
  }, timeoutMs);

  if (userSignal) {
    userSignal.addEventListener("abort", () => {
      clearTimeout(timeoutId);
      controller.abort(userSignal.reason);
    });
  }

  const headers = new Headers(customHeaders);
  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }

  // Attach auth token if available in browser localStorage
  if (typeof window !== "undefined" && !headers.has("Authorization")) {
    const token = localStorage.getItem("bioinsight_token");
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  let requestBody: BodyInit | undefined;
  if (body !== undefined && body !== null) {
    if (body instanceof FormData || body instanceof URLSearchParams || body instanceof Blob) {
      requestBody = body;
    } else {
      if (!headers.has("Content-Type")) {
        headers.set("Content-Type", "application/json");
      }
      requestBody = JSON.stringify(body);
    }
  }

  try {
    const response = await fetch(url.toString(), {
      ...fetchOptions,
      headers,
      body: requestBody,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    const contentType = response.headers.get("content-type") || "";
    let data: unknown;

    if (contentType.includes("application/json")) {
      try {
        data = await response.json();
      } catch {
        data = null;
      }
    } else {
      data = await response.text();
    }

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status} (${response.statusText})`;
      if (typeof data === "object" && data !== null && "detail" in data) {
        const detail = (data as { detail: unknown }).detail;
        if (typeof detail === "string") {
          errorMessage = detail;
        } else if (typeof detail === "object" && detail !== null) {
          errorMessage = JSON.stringify(detail);
        }
      }
      throw new ApiError(response.status, response.statusText, data, errorMessage);
    }

    return data as T;
  } catch (err) {
    clearTimeout(timeoutId);

    if (err instanceof ApiError) {
      throw err;
    }

    if (err instanceof Error) {
      if (err.name === "AbortError" || controller.signal.aborted) {
        throw new NetworkError("Request was cancelled or timed out", err);
      }
      throw new NetworkError(`Network connection failed: ${err.message}`, err);
    }

    throw new NetworkError("Unknown network error occurred", err);
  }
}

