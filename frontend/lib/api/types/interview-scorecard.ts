export type InterviewRecommendation =
  | "strong_yes"
  | "yes"
  | "mixed"
  | "no";

export type InterviewScorecardStatus = "draft" | "completed";

export type InterviewScorecardSummary = {
  status: InterviewScorecardStatus;
  completed_criteria_count: number;
  total_criteria_count: number;
  average_rating: number | null;
  strongest_dimensions: string[];
  weakest_dimensions: string[];
  unanswered_dimensions: string[];
  recommendation: InterviewRecommendation | null;
};

export type InterviewScorecard = {
  id: string;
  vacancy_id: string;
  candidate_id: string;
  status: InterviewScorecardStatus;
  technical_competency: number | null;
  experience_relevance: number | null;
  communication: number | null;
  ownership: number | null;
  interview_summary: string | null;
  interview_notes: string | null;
  recommendation: InterviewRecommendation | null;
  summary: InterviewScorecardSummary;
  created_at: string;
  updated_at: string;
};

export type InterviewScorecardInput = {
  status: InterviewScorecardStatus;
  technical_competency: number | null;
  experience_relevance: number | null;
  communication: number | null;
  ownership: number | null;
  interview_summary: string | null;
  interview_notes: string | null;
  recommendation: InterviewRecommendation | null;
};

export const INTERVIEW_RECOMMENDATIONS: readonly InterviewRecommendation[] = [
  "strong_yes",
  "yes",
  "mixed",
  "no"
] as const;

export const INTERVIEW_RECOMMENDATION_LABELS: Record<InterviewRecommendation, string> = {
  strong_yes: "Strong yes",
  yes: "Yes",
  mixed: "Mixed",
  no: "No"
};

export const INTERVIEW_SCORECARD_STATUS_LABELS: Record<InterviewScorecardStatus, string> = {
  draft: "Draft",
  completed: "Completed"
};
