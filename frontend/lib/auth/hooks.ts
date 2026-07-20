"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

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

/**
 * Session token lives in sessionStorage, so it is unavailable during SSR.
 * Gate token reads behind a post-mount flag so the first client render matches
 * the server tree (both treat auth as "not ready" / loading).
 */
export function useCurrentUser() {
  const [authReady, setAuthReady] = useState(false);

  useEffect(() => {
    setAuthReady(true);
  }, []);

  const hasToken = authReady && getAccessToken() !== null;

  const query = useQuery({
    queryKey: currentUserQueryKey,
    queryFn: getCurrentUser,
    enabled: hasToken
  });

  return {
    ...query,
    isLoading: !authReady || query.isLoading,
    isPending: !authReady || query.isPending
  };
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
