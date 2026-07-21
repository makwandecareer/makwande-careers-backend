import { api } from "@/lib/client-api";

export type AITool =
  | "roadmap"
  | "skills-gap"
  | "interview-prep"
  | "cover-letter"
  | "improve-summary"
  | "improve-experience"
  | "job-match";

export const AI_TOOL_LABELS: Record<AITool, string> = {
  roadmap: "Career roadmap",
  "skills-gap": "Skills gap",
  "interview-prep": "Interview preparation",
  "cover-letter": "Cover letter",
  "improve-summary": "Improve summary",
  "improve-experience": "Improve experience",
  "job-match": "Job match",
};

export async function runCareerAI<T>(tool: AITool, payload: Record<string, unknown>) {
  return api<T>(`/api/ai-career/${tool}`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
