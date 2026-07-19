export type DashboardGitHubSummary = {
  connected: boolean;
  repositories: number;
};

export type DashboardEvidenceSummary = {
  count: number;
};

export type DashboardPassportSummary = {
  skills: number;
  top_skills: string[];
};

export type DashboardRoadmapSummary = {
  items: number;
};

export type CandidateDashboardResponse = {
  github: DashboardGitHubSummary;
  evidence: DashboardEvidenceSummary;
  passport: DashboardPassportSummary;
  roadmap: DashboardRoadmapSummary;
};
