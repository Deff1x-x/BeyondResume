import { apiRequest } from "@/lib/api/client";
import type {
  CareerCompanionAction,
  CareerCompanionChatResponse,
  CareerCompanionGenerateRequest,
  CareerCompanionPlan
} from "@/lib/api/types/career-companion";

export function getCareerCompanionPlan() {
  return apiRequest<CareerCompanionPlan>("/candidate/career-companion");
}

export function generateCareerCompanionPlan(payload: CareerCompanionGenerateRequest) {
  return apiRequest<CareerCompanionPlan>("/candidate/career-companion/generate", {
    method: "POST",
    body: payload
  });
}

export function patchCareerCompanionAction(
  actionId: string,
  status: "accepted" | "in_progress" | "awaiting_evidence" | "dismissed"
) {
  return apiRequest<CareerCompanionAction>(
    `/candidate/career-companion/actions/${encodeURIComponent(actionId)}`,
    {
      method: "PATCH",
      body: { status }
    }
  );
}

export function postCareerCompanionChat(message: string) {
  return apiRequest<CareerCompanionChatResponse>("/candidate/career-companion/chat", {
    method: "POST",
    body: { message }
  });
}

export function refreshCareerCompanionFromEvidence() {
  return apiRequest<CareerCompanionPlan>("/candidate/career-companion/refresh-from-evidence", {
    method: "POST"
  });
}
