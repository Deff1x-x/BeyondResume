export type ApiErrorDetail = {
  field?: string;
  issue?: string;
  max_bytes?: number;
  max_length?: number;
  [key: string]: unknown;
};

export type ApiErrorPayload = {
  code: string;
  message: string;
  details: ApiErrorDetail[];
  request_id: string;
};

export type ApiErrorEnvelope = {
  error: ApiErrorPayload;
};
