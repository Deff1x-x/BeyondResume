import { apiRequest } from "@/lib/api/client";
import type {
  GitHubRepositoryConnectRequest,
  GitHubRepositoryDetailResponse,
  GitHubRepositoryResponse
} from "@/lib/api/types/github";
import type { JobPollingResponse } from "@/lib/api/types/jobs";

export function listGitHubRepositories(): Promise<GitHubRepositoryResponse[]> {
  return apiRequest<GitHubRepositoryResponse[]>("/candidate/github/repositories");
}

export function connectGitHubRepository(
  request: GitHubRepositoryConnectRequest
): Promise<GitHubRepositoryResponse> {
  return apiRequest<GitHubRepositoryResponse>("/candidate/github/repositories", {
    method: "POST",
    body: request
  });
}

export function getGitHubRepository(
  repositoryId: string
): Promise<GitHubRepositoryDetailResponse> {
  return apiRequest<GitHubRepositoryDetailResponse>(
    `/candidate/github/repositories/${repositoryId}`
  );
}

export function analyzeGitHubRepository(
  repositoryId: string
): Promise<JobPollingResponse> {
  return apiRequest<JobPollingResponse>(
    `/candidate/github/repositories/${repositoryId}/analyze`,
    { method: "POST" }
  );
}

export function deleteGitHubRepository(repositoryId: string): Promise<void> {
  return apiRequest<void>(`/candidate/github/repositories/${repositoryId}`, {
    method: "DELETE"
  });
}
