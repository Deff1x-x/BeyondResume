import { ApiClientError, parseApiErrorResponse } from "@/lib/api/error";
import { clearAccessToken, getAccessToken } from "@/lib/auth/token";

const API_PREFIX = "/api/v1";

export type ApiRequestOptions = {
  method?: string;
  body?: BodyInit | Record<string, unknown> | unknown[] | null;
  headers?: HeadersInit;
  signal?: AbortSignal;
};

function assertRelativeApiPath(path: string): string {
  if (path.length === 0) {
    throw new Error("API path must not be empty");
  }

  if (/^[a-zA-Z][a-zA-Z\d+\-.]*:/.test(path) || path.startsWith("//")) {
    throw new Error("Absolute URLs are not allowed in apiRequest");
  }

  return path.startsWith("/") ? path : `/${path}`;
}

function hasHeader(headers: Headers, name: string): boolean {
  return headers.has(name);
}

function buildHeaders(options: ApiRequestOptions | undefined, body: BodyInit | undefined): Headers {
  const headers = new Headers(options?.headers);

  if (!hasHeader(headers, "Authorization")) {
    const token = getAccessToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  const isFormData = typeof FormData !== "undefined" && body instanceof FormData;
  if (body !== undefined && !isFormData && !hasHeader(headers, "Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  return headers;
}

function serializeBody(
  body: ApiRequestOptions["body"]
): BodyInit | undefined {
  if (body === undefined || body === null) {
    return undefined;
  }

  if (
    typeof body === "string" ||
    body instanceof FormData ||
    body instanceof Blob ||
    body instanceof ArrayBuffer ||
    ArrayBuffer.isView(body) ||
    body instanceof URLSearchParams
  ) {
    return body;
  }

  return JSON.stringify(body);
}

/**
 * Thin fetch wrapper for same-origin `/api/v1` requests.
 *
 * - `path` is relative to `/api/v1` (e.g. `/auth/login`, `/me`).
 * - Absolute URLs are rejected.
 * - On HTTP 204, resolves to `undefined` (use `apiRequest<void>`).
 * - On non-2xx, throws `ApiClientError` and clears the access token on 401.
 */
export async function apiRequest<TResponse>(
  path: string,
  options?: ApiRequestOptions
): Promise<TResponse> {
  const normalizedPath = assertRelativeApiPath(path);
  const body = serializeBody(options?.body);
  const headers = buildHeaders(options, body);

  const response = await fetch(`${API_PREFIX}${normalizedPath}`, {
    method: options?.method ?? "GET",
    headers,
    body,
    signal: options?.signal
  });

  if (response.status === 401) {
    clearAccessToken();
  }

  if (!response.ok) {
    throw await parseApiErrorResponse(response);
  }

  if (response.status === 204) {
    return undefined as TResponse;
  }

  const text = await response.text();
  if (!text) {
    return undefined as TResponse;
  }

  try {
    return JSON.parse(text) as TResponse;
  } catch {
    throw new ApiClientError({
      status: response.status,
      code: "INVALID_JSON",
      message: "Response body is not valid JSON",
      details: [],
      requestId: null
    });
  }
}
