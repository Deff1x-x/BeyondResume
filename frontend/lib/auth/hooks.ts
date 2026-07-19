"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  getCurrentUser,
  isTokenResponse,
  login,
  logout,
  register
} from "@/lib/api/auth";
import type {
  LoginRequest,
  RegisterRequest,
  RegisterSuccessResponse,
  TokenResponse
} from "@/lib/api/types/auth";
import { getAccessToken, setAccessToken } from "@/lib/auth/token";

export const currentUserQueryKey = ["me"] as const;

export function useCurrentUser() {
  return useQuery({
    queryKey: currentUserQueryKey,
    queryFn: getCurrentUser,
    enabled: typeof window !== "undefined" && getAccessToken() !== null
  });
}

export function useLogin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: LoginRequest) => login(payload),
    onSuccess: async (data: TokenResponse) => {
      setAccessToken(data.access_token);
      await queryClient.invalidateQueries({ queryKey: currentUserQueryKey });
    }
  });
}

export function useRegister() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: RegisterRequest) => register(payload),
    onSuccess: async (data: RegisterSuccessResponse) => {
      if (!isTokenResponse(data)) {
        return;
      }

      setAccessToken(data.access_token);
      await queryClient.invalidateQueries({ queryKey: currentUserQueryKey });
    }
  });
}

/**
 * Frontend-only logout: clear access token and React Query cache.
 * Navigation stays in UI components (callers).
 */
export function useLogout() {
  const queryClient = useQueryClient();

  return () => {
    logout();
    queryClient.clear();
  };
}
