import { apiRequest } from "@/lib/api/client";
import type {
  EvidenceHubListResponse,
  EvidenceHubQueryParams
} from "@/lib/api/types/evidence";

function toQueryString(params: EvidenceHubQueryParams): string {
  const search = new URLSearchParams();

  if (params.source_type) {
    search.set("source_type", params.source_type);
  }
  if (params.skill?.trim()) {
    search.set("skill", params.skill.trim());
  }
  if (params.search?.trim()) {
    search.set("search", params.search.trim());
  }
  if (params.limit != null) {
    search.set("limit", String(params.limit));
  }
  if (params.offset != null) {
    search.set("offset", String(params.offset));
  }

  const query = search.toString();
  return query ? `?${query}` : "";
}

export function listCandidateEvidence(
  params: EvidenceHubQueryParams = {}
): Promise<EvidenceHubListResponse> {
  return apiRequest<EvidenceHubListResponse>(`/candidate/evidence${toQueryString(params)}`);
}
