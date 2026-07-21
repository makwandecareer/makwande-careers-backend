import type { StudioDraft } from "@/lib/cv-studio";

export type StoredCV = {
  id: string;
  owner_id: string;
  title: string;
  target_role: string | null;
  template_key: string;
  content: StudioDraft;
  is_public_to_employers: boolean;
  version: number;
  created_at: string;
  updated_at: string;
};

export type StoredCVVersion = {
  id: string;
  cv_id: string;
  owner_id: string;
  version: number;
  title: string;
  target_role: string | null;
  template_key: string;
  content: StudioDraft;
  created_at: string;
};

export function cvPayload(draft: StudioDraft) {
  return {
    title: draft.cvTitle.trim() || "Untitled CV",
    target_role: draft.targetRole.trim() || null,
    template_key: draft.templateKey || "ats-standard",
    content: draft,
  };
}
