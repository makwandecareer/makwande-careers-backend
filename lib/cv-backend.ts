import { api } from "@/lib/client-api";
import type { StudioDraft } from "@/lib/cv-studio";

export type SavedCV = {
  id: string;
  owner_id: string;
  title: string;
  target_role: string | null;
  template_key: string;
  content: StudioDraft;
  version: number;
  created_at: string;
  updated_at: string;
};

export type SavedCVVersion = {
  id: string;
  cv_id: string;
  version_number: number;
  title: string;
  target_role: string | null;
  template_key: string;
  content: StudioDraft;
  created_at: string;
};

export async function createSavedCV(draft: StudioDraft): Promise<SavedCV> {
  return api<SavedCV>("/api/cvs", {
    method: "POST",
    body: JSON.stringify({
      title: draft.cvTitle,
      target_role: draft.targetRole,
      template_key: draft.templateKey,
      content: draft,
    }),
  });
}

export async function updateSavedCV(
  cvId: string,
  draft: StudioDraft,
): Promise<SavedCV> {
  return api<SavedCV>(`/api/cvs/${cvId}`, {
    method: "PUT",
    body: JSON.stringify({
      title: draft.cvTitle,
      target_role: draft.targetRole,
      template_key: draft.templateKey,
      content: draft,
    }),
  });
}

export async function listSavedCVs(): Promise<SavedCV[]> {
  return api<SavedCV[]>("/api/cvs");
}

export async function getSavedCV(cvId: string): Promise<SavedCV> {
  return api<SavedCV>(`/api/cvs/${cvId}`);
}

export async function deleteSavedCV(cvId: string): Promise<void> {
  return api<void>(`/api/cvs/${cvId}`, { method: "DELETE" });
}

export async function duplicateSavedCV(cvId: string): Promise<SavedCV> {
  return api<SavedCV>(`/api/cvs/${cvId}/duplicate`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function listCVVersions(
  cvId: string,
): Promise<SavedCVVersion[]> {
  return api<SavedCVVersion[]>(`/api/cvs/${cvId}/versions`);
}

export async function restoreCVVersion(
  cvId: string,
  versionId: string,
): Promise<SavedCV> {
  return api<SavedCV>(
    `/api/cvs/${cvId}/versions/${versionId}/restore`,
    { method: "POST" },
  );
}
