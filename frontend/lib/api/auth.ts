import { apiRequest } from "@/lib/api/client";
import type {
  LoginRequest,
  PublicUserResponse,
  RegisterRequest,
  RegisterSuccessResponse,
  TokenResponse
} from "@/lib/api/types/auth";
import { clearAccessToken } from "@/lib/auth/token";

export function isTokenResponse(response: RegisterSuccessResponse): response is TokenResponse {
  return (
    typeof response === "object" &&
    response !== null &&
    "access_token" in response &&
    typeof response.access_token === "string"
  );
}

export async function register(payload: RegisterRequest): Promise<RegisterSuccessResponse> {
  return apiRequest<RegisterSuccessResponse>("/auth/register", {
    method: "POST",
    body: payload
  });
}

export async function login(payload: LoginRequest): Promise<TokenResponse> {
  return apiRequest<TokenResponse>("/auth/login", {
    method: "POST",
    body: payload
  });
}

export async function getCurrentUser(): Promise<PublicUserResponse> {
  return apiRequest<PublicUserResponse>("/me");
}

/** Frontend-only logout: clears the access token from sessionStorage. */
export function logout(): void {
  clearAccessToken();
}
