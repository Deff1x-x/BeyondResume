"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { getDemoStatus, resetDemo, startDemo } from "@/lib/api/demo";
import type { Role } from "@/lib/api/types/auth";
import { currentUserQueryKey } from "@/lib/auth/hooks";
import { clearAccessToken, setAccessToken } from "@/lib/auth/token";

const DEMO_SESSION_KEY = "beyondresume_demo_session";

export function markDemoSession(role: Role): void {
  if (typeof window === "undefined") {
    return;
  }
  sessionStorage.setItem(DEMO_SESSION_KEY, role);
}

export function clearDemoSession(): void {
  if (typeof window === "undefined") {
    return;
  }
  sessionStorage.removeItem(DEMO_SESSION_KEY);
}

export function getDemoSessionRole(): Role | null {
  if (typeof window === "undefined") {
    return null;
  }
  const value = sessionStorage.getItem(DEMO_SESSION_KEY);
  return value === "candidate" || value === "employer" ? value : null;
}

export function useDemoStatus() {
  return useQuery({
    queryKey: ["demo", "status"],
    queryFn: getDemoStatus,
    staleTime: 60_000,
    retry: false
  });
}

export function useStartDemo() {
  const queryClient = useQueryClient();
  const router = useRouter();

  return useMutation({
    mutationFn: (role: Role) => startDemo({ role }),
    onSuccess: async (data, role) => {
      setAccessToken(data.access_token);
      markDemoSession(role);
      await queryClient.clear();
      await queryClient.invalidateQueries({ queryKey: currentUserQueryKey });
      router.push("/");
    }
  });
}

export function useResetDemo() {
  const queryClient = useQueryClient();
  const router = useRouter();

  return useMutation({
    mutationFn: () => resetDemo(),
    onSuccess: async (data) => {
      setAccessToken(data.access_token);
      markDemoSession(data.role);
      await queryClient.clear();
      await queryClient.invalidateQueries({ queryKey: currentUserQueryKey });
      router.push("/");
      router.refresh();
    }
  });
}

export function useExitDemo() {
  const queryClient = useQueryClient();
  const router = useRouter();

  return () => {
    clearAccessToken();
    clearDemoSession();
    queryClient.clear();
    router.push("/landing");
  };
}
