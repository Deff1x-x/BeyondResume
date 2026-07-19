import { apiRequest } from "@/lib/api/client";
import type { RoadmapResponse } from "@/lib/api/types/roadmap";

export function getRoadmap(): Promise<RoadmapResponse> {
  return apiRequest<RoadmapResponse>("/candidate/roadmap");
}
