export type OnboardingStatus = "profile_required";

export type CandidateProfileResponse = {
  id: string;
  display_name: string | null;
  target_role: string | null;
  location: string | null;
  remote_preference: string | null;
  english_level: string | null;
  availability: string | null;
  summary: string | null;
  data_processing_consent: boolean | null;
  onboarding_status: OnboardingStatus;
  salary_expectation: string | null;
  preferred_employment_type: string | null;
  relocation_readiness: boolean | null;
  portfolio_url: string | null;
  linkedin_url: string | null;
};

export type CandidateProfilePatchRequest = {
  display_name?: string | null;
  target_role?: string | null;
  location?: string | null;
  remote_preference?: string | null;
  english_level?: string | null;
  availability?: string | null;
  summary?: string | null;
  data_processing_consent?: boolean | null;
  salary_expectation?: string | null;
  preferred_employment_type?: string | null;
  relocation_readiness?: boolean | null;
  portfolio_url?: string | null;
  linkedin_url?: string | null;
};
