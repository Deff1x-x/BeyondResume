"use client";

import { useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  analyzeGitHubRepository,
  connectGitHubRepository,
  deleteGitHubRepository,
  getGitHubRepository,
  listGitHubRepositories,
  listGitHubRepositoryEvidence
} from "@/lib/api/github";
import type { GitHubRepositoryConnectRequest } from "@/lib/api/types/github";
import { isTerminalJobStatus, jobQueryKey, useJobQuery } from "@/lib/jobs/hooks";
import { roadmapQueryKey } from "@/lib/roadmap/hooks";
import { skillPassportQueryKey } from "@/lib/skill-passport/hooks";

export const githubRepositoriesQueryKey = ["github", "repositories"] as const;

export function githubRepositoryQueryKey(repositoryId: string) {
  return ["github", "repository", repositoryId] as const;
}

export function useGitHubRepositoriesQuery(enabled: boolean) {
  return useQuery({
    queryKey: githubRepositoriesQueryKey,
    queryFn: listGitHubRepositories,
    enabled,
    staleTime: 60_000,
    gcTime: 300_000
  });
}

export function useGitHubRepositoryQuery(repositoryId: string, enabled: boolean) {
  return useQuery({
    queryKey: githubRepositoryQueryKey(repositoryId),
    queryFn: () => getGitHubRepository(repositoryId),
    enabled,
    staleTime: 60_000,
    gcTime: 300_000
  });
}

export function githubRepositoryEvidenceQueryKey(repositoryId: string) {
  return [...githubRepositoryQueryKey(repositoryId), "evidence"] as const;
}

export function useGitHubRepositoryEvidenceQuery(repositoryId: string, enabled: boolean) {
  return useQuery({
    queryKey: githubRepositoryEvidenceQueryKey(repositoryId),
    queryFn: () => listGitHubRepositoryEvidence(repositoryId),
    enabled,
    staleTime: 60_000,
    gcTime: 300_000
  });
}

export function useConnectGitHubRepository() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: GitHubRepositoryConnectRequest) =>
      connectGitHubRepository(request),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: githubRepositoriesQueryKey });
    }
  });
}

export function useStartGitHubScan() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (repositoryId: string) => analyzeGitHubRepository(repositoryId),
    onSuccess: (job) => {
      queryClient.setQueryData(jobQueryKey(job.id), job);
      void queryClient.invalidateQueries({ queryKey: githubRepositoriesQueryKey });
    }
  });
}

/**
 * Polls a github_scan job and refreshes repository data once it reaches a
 * terminal status.
 */
export function useGitHubScanJobQuery(jobId: string | null, repositoryId: string) {
  const queryClient = useQueryClient();
  const query = useJobQuery(jobId);
  const status = query.data?.status;

  useEffect(() => {
    if (isTerminalJobStatus(status)) {
      void queryClient.invalidateQueries({ queryKey: githubRepositoriesQueryKey });
      void queryClient.invalidateQueries({
        queryKey: githubRepositoryQueryKey(repositoryId)
      });
      void queryClient.invalidateQueries({ queryKey: skillPassportQueryKey });
      void queryClient.invalidateQueries({ queryKey: roadmapQueryKey });
    }
  }, [status, queryClient, repositoryId]);

  return query;
}

export function useDeleteGitHubRepository() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (repositoryId: string) => deleteGitHubRepository(repositoryId),
    onSuccess: (_data, repositoryId) => {
      queryClient.removeQueries({ queryKey: githubRepositoryQueryKey(repositoryId) });
      void queryClient.invalidateQueries({ queryKey: githubRepositoriesQueryKey });
      void queryClient.invalidateQueries({ queryKey: skillPassportQueryKey });
      void queryClient.invalidateQueries({ queryKey: roadmapQueryKey });
    }
  });
}
