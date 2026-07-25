export type AiHiringVerdict =
  | "strong_hire"
  | "hire"
  | "consider"
  | "insufficient_evidence"
  | "do_not_hire";

export type AiHiringIntelligence = {
  verdict: AiHiringVerdict;
  confidence: number;
  executive_summary: string;
  strengths: string[];
  hiring_risks: string[];
  confidence_explanation: string[];
  first_90_days_focus: string[];
  recommended_next_action: string;
};
