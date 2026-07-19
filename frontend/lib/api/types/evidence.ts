export type EvidenceHubSkill = {
  id: string;
  name: string;
  category: string;
  extraction_method: string;
  evidence_confidence: number;
};

export type EvidenceHubSource = {
  label: string;
  document_name?: string | null;
  parsed_at?: string | null;
  repository_name?: string | null;
  repository_url?: string | null;
};

export type EvidenceHubItem = {
  id: string;
  source_type: string;
  source_reference: string | null;
  title: string | null;
  description: string | null;
  verification_status: string | null;
  strength: number | null;
  created_at: string;
  updated_at: string;
  skills: EvidenceHubSkill[];
  source: EvidenceHubSource;
};

export type EvidenceHubListResponse = {
  items: EvidenceHubItem[];
  total: number;
  limit: number;
  offset: number;
};

export type EvidenceHubQueryParams = {
  source_type?: string;
  skill?: string;
  search?: string;
  limit?: number;
  offset?: number;
};
