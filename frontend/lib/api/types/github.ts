import type { JobPollingResponse } from "@/lib/api/types/jobs";

export type GitHubRepositoryResponse = {
  id: string;
  repository_url: string;
  created_at: string;
  job: JobPollingResponse | null;
};

export type GitHubRepositorySnapshotSummary = {
  description: string | null;
  is_archived: boolean | null;
  languages: string[];
  file_count: number;
  manifest_count: number;
};

export type GitHubRepositorySkill = {
  name: string;
  category: string;
  extraction_confidence: number;
};

export type GitHubRepositoryDetailResponse = GitHubRepositoryResponse & {
  snapshot: GitHubRepositorySnapshotSummary | null;
  skills: GitHubRepositorySkill[];
};

export type GitHubRepositoryConnectRequest = {
  repository_url: string;
};
