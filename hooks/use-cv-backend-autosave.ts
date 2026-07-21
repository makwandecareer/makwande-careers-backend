"use client";

import { useEffect, useRef, useState } from "react";
import type { StudioDraft } from "@/lib/cv-studio";
import {
  createSavedCV,
  updateSavedCV,
  type SavedCV,
} from "@/lib/cv-backend";

const ACTIVE_CV_KEY = "makwande_active_cv_id";

export function useCVBackendAutosave(
  draft: StudioDraft | null,
  delay = 2500,
) {
  const [savedCV, setSavedCV] = useState<SavedCV | null>(null);
  const [state, setState] = useState<
    "idle" | "saving" | "saved" | "error"
  >("idle");
  const [error, setError] = useState("");
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const firstRun = useRef(true);

  useEffect(() => {
    if (!draft) return;

    if (firstRun.current) {
      firstRun.current = false;
      return;
    }

    if (timer.current) {
      clearTimeout(timer.current);
    }

    timer.current = setTimeout(async () => {
      setState("saving");
      setError("");

      try {
        const activeId = localStorage.getItem(ACTIVE_CV_KEY);

        const result = activeId
          ? await updateSavedCV(activeId, draft)
          : await createSavedCV(draft);

        localStorage.setItem(ACTIVE_CV_KEY, result.id);
        setSavedCV(result);
        setState("saved");
      } catch (reason) {
        setError(
          reason instanceof Error
            ? reason.message
            : "Backend autosave failed",
        );
        setState("error");
      }
    }, delay);

    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, [draft, delay]);

  return {
    savedCV,
    backendSaveState: state,
    backendSaveError: error,
  };
}
