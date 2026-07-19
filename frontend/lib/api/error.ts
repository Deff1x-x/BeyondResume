import type { ApiErrorDetail, ApiErrorEnvelope } from "@/lib/api/types/error";

const FALLBACK_CODE = "UNKNOWN_ERROR";
const FALLBACK_MESSAGE = "Request failed";

export class ApiClientError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: ApiErrorDetail[];
  readonly requestId: string | null;

  constructor(params: {
    status: number;
    code: string;
    message: string;
    details?: ApiErrorDetail[];
    requestId?: string | null;
  }) {
    super(params.message);
    this.name = "ApiClientError";
    this.status = params.status;
    this.code = params.code;
    this.details = params.details ?? [];
    this.requestId = params.requestId ?? null;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function parseDetail(value: unknown): ApiErrorDetail | null {
  if (!isRecord(value)) {
    return null;
  }

  const detail: ApiErrorDetail = { ...value };

  if ("field" in value && value.field !== undefined && typeof value.field !== "string") {
    delete detail.field;
  }
  if ("issue" in value && value.issue !== undefined && typeof value.issue !== "string") {
    delete detail.issue;
  }
  if ("max_bytes" in value && value.max_bytes !== undefined && typeof value.max_bytes !== "number") {
    delete detail.max_bytes;
  }
  if (
    "max_length" in value &&
    value.max_length !== undefined &&
    typeof value.max_length !== "number"
  ) {
    delete detail.max_length;
  }

  return detail;
}

function isApiErrorEnvelope(value: unknown): value is ApiErrorEnvelope {
  if (!isRecord(value) || !isRecord(value.error)) {
    return false;
  }

  const error = value.error;
  return (
    typeof error.code === "string" &&
    typeof error.message === "string" &&
    Array.isArray(error.details) &&
    typeof error.request_id === "string"
  );
}

export async function parseApiErrorResponse(response: Response): Promise<ApiClientError> {
  const status = response.status;
  let payload: unknown;

  try {
    const text = await response.text();
    if (!text) {
      return new ApiClientError({
        status,
        code: FALLBACK_CODE,
        message: FALLBACK_MESSAGE,
        details: [],
        requestId: null
      });
    }

    try {
      payload = JSON.parse(text) as unknown;
    } catch {
      return new ApiClientError({
        status,
        code: FALLBACK_CODE,
        message: FALLBACK_MESSAGE,
        details: [],
        requestId: null
      });
    }
  } catch {
    return new ApiClientError({
      status,
      code: FALLBACK_CODE,
      message: FALLBACK_MESSAGE,
      details: [],
      requestId: null
    });
  }

  if (!isApiErrorEnvelope(payload)) {
    return new ApiClientError({
      status,
      code: FALLBACK_CODE,
      message: FALLBACK_MESSAGE,
      details: [],
      requestId: null
    });
  }

  const details = payload.error.details
    .map(parseDetail)
    .filter((detail): detail is ApiErrorDetail => detail !== null);

  return new ApiClientError({
    status,
    code: payload.error.code,
    message: payload.error.message,
    details,
    requestId: payload.error.request_id
  });
}
