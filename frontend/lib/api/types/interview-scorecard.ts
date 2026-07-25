export type InterviewRecommendation =
  | "strong_yes"
  | "yes"
  | "mixed"
  | "no";

export type InterviewScorecard = {
  id: string;
  vacancy_id: string;
  candidate_id: string;
  technical_competency: number;
  experience_relevance: number;
  communication: number;
  ownership: number;
  interview_summary: string | null;
  interview_notes: string | null;
  recommendation: InterviewRecommendation;
  created_at: string;
  updated_at: string;
};

export type InterviewScorecardInput = {
  technical_competency: number;
  experience_relevance: number;
  communication: number;
  ownership: number;
  interview_summary: string | null;
  interview_notes: string | null;
  recommendation: InterviewRecommendation;
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
