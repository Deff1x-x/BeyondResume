export type CompanionMode =
  | "target_vacancy"
  | "target_role"
  | "career_growth"
  | "explore_direction";

export type ActionHorizon = "fix_now" | "build_next" | "grow_further";

export type ActionType =
  | "improve_existing_project"
  | "build_new_project"
  | "learn_foundation";

export type ActionStatus =
  | "suggested"
  | "accepted"
  | "in_progress"
  | "awaiting_evidence"
  | "evidence_detected"
  | "partially_verified"
  | "completed"
  | "dismissed";

export type CareerCompanionActionSkill = {
  skill_id: string;
  skill_name: string;
  role: "gap" | "potential_cover" | "related";
};

export type CareerCompanionAction = {
  id: string;
  horizon: ActionHorizon;
  action_type: ActionType;
  status: ActionStatus;
  title: string;
  description: string;
  why_it_matters: string;
  implementation_steps: string[];
  expected_artifacts: string[];
  verification_method: string;
  estimated_effort: string;
  github_repository_id: string | null;
  project_label: string | null;
  current_target_impact: Record<string, unknown>;
  career_growth_impact: Record<string, unknown>;
  priority_score: number;
  priority_explanation: string;
  sort_order: number;
  skills: CareerCompanionActionSkill[];
};

export type CareerCompanionProgressEvent = {
  id: string;
  event_type: string;
  title: string;
  detail: string;
  payload: Record<string, unknown>;
  created_at: string;
};

export type CareerCompanionChatMessage = {
  id: string;
  role: string;
  content: string;
  revision_applied: string | null;
  created_at: string;
};

export type CareerCompanionPlan = {
  id: string;
  mode: CompanionMode;
  target_vacancy_id: string | null;
  target_role: string | null;
  status: string;
  generation_mode: "live" | "mock" | "fallback";
  summary: Record<string, unknown>;
  current_position: {
    goal_label?: string;
    verified_skills?: string[];
    missing_required_skills?: string[];
    missing_preferred_skills?: string[];
    weak_evidence?: string[];
    strongest_projects?: Array<{ id: string; label: string; repository_url: string }>;
    readiness?: string;
    target_match_score?: number | null;
    explore_directions?: string[];
    next_level_titles?: string[];
    has_resume?: boolean;
    mode?: string;
  };
  actions: CareerCompanionAction[];
  progress_events: CareerCompanionProgressEvent[];
  chat_messages: CareerCompanionChatMessage[];
};

export type CareerCompanionGenerateRequest = {
  mode: CompanionMode;
  target_vacancy_id?: string | null;
  target_role?: string | null;
};

export type CareerCompanionChatResponse = {
  message: CareerCompanionChatMessage;
  plan: CareerCompanionPlan | null;
};
