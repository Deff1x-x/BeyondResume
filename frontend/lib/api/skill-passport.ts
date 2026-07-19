import { apiRequest } from "@/lib/api/client";
import type { SkillPassportResponse } from "@/lib/api/types/skill-passport";

export function getSkillPassport(): Promise<SkillPassportResponse> {
  return apiRequest<SkillPassportResponse>("/candidate/skill-passport");
}
