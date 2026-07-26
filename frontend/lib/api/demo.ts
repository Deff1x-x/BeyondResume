import { apiRequest } from "@/lib/api/client";
import type { Role, TokenResponse } from "@/lib/api/types/auth";

export type DemoStatusResponse = {
  enabled: boolean;
  roles: Role[];
};

export type DemoStartRequest = {
  role: Role;
};

export type DemoResetResponse = {
  ok: true;
  role: Role;
  access_token: string;
  token_type: "bearer";
};

export function getDemoStatus(): Promise<DemoStatusResponse> {
  return apiRequest<DemoStatusResponse>("/demo/status");
}

export function startDemo(payload: DemoStartRequest): Promise<TokenResponse> {
  return apiRequest<TokenResponse>("/demo/start", {
    method: "POST",
    body: payload
  });
}

export function resetDemo(): Promise<DemoResetResponse> {
  return apiRequest<DemoResetResponse>("/demo/reset", {
    method: "POST"
  });
}
