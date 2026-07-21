"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/client-api";
import {
  createStudioDraft,
  type StudioDraft,
  type StudioSection,
} from "@/lib/cv-studio";
import type { ProfileBundle } from "@/lib/types";
import {
  applyTemplateToDraft,
  buildExportPayload,
  readSelectedTemplate,
  STUDIO_DRAFT_KEY,
} from "@/lib/template-process";
import { Toolbar } from "./Toolbar";
import { SectionSidebar } from "./SectionSidebar";
import { EditorPanel } from "./EditorPanel";
import { PreviewPanel } from "./PreviewPanel";
import { DesignPanel } from "./DesignPanel";

export function CVStudio() {
  const [draft, setDraft] = useState<StudioDraft | null>(null);
  const [active, setActive] = useState<StudioSection>("profile");
  const [mode, setMode] = useState<"content" | "design">("content");
  const [history, setHistory] = useState<StudioDraft[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [saveState, setSaveState] = useState<
    "saved" | "saving" | "unsaved"
  >("saved");
  const [zoom, setZoom] = useState(0.82);
  const [preview, setPreview] = useState(false);
  const [error, setError] = useState("");
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    api<ProfileBundle>("/api/profile/source-of-truth")
      .then((bundle) => {
        let initial = createStudioDraft(bundle);

        const savedDraft = localStorage.getItem(STUDIO_DRAFT_KEY);

        if (savedDraft) {
          try {
            initial = {
              ...initial,
              ...(JSON.parse(savedDraft) as Partial<StudioDraft>),
            };
          } catch {
            localStorage.removeItem(STUDIO_DRAFT_KEY);
          }
        }

        const selectedTemplate = readSelectedTemplate();

        if (
          selectedTemplate &&
          selectedTemplate.key !== initial.templateKey
        ) {
          initial = applyTemplateToDraft(
            initial,
            selectedTemplate,
          );

          localStorage.setItem(
            STUDIO_DRAFT_KEY,
            JSON.stringify(initial),
          );
        }

        setDraft(initial);
        setHistory([initial]);
        setHistoryIndex(0);
      })
      .catch((reason) =>
        setError(
          reason instanceof Error
            ? reason.message
            : "Unable to open CV Studio",
        ),
      );
  }, []);

  function persist(nextDraft: StudioDraft) {
    setSaveState("saving");

    if (saveTimer.current) {
      clearTimeout(saveTimer.current);
    }

    saveTimer.current = setTimeout(() => {
      localStorage.setItem(
        STUDIO_DRAFT_KEY,
        JSON.stringify(nextDraft),
      );
      setSaveState("saved");
    }, 900);
  }

  function change(nextDraft: StudioDraft) {
    const nextHistory = [
      ...history.slice(0, historyIndex + 1),
      nextDraft,
    ].slice(-50);

    setHistory(nextHistory);
    setHistoryIndex(nextHistory.length - 1);
    setDraft(nextDraft);
    setSaveState("unsaved");
    persist(nextDraft);
  }

  function undo() {
    if (historyIndex <= 0) return;

    const nextIndex = historyIndex - 1;
    const previousDraft = history[nextIndex];

    setHistoryIndex(nextIndex);
    setDraft(previousDraft);
    persist(previousDraft);
  }

  function redo() {
    if (historyIndex >= history.length - 1) return;

    const nextIndex = historyIndex + 1;
    const nextDraft = history[nextIndex];

    setHistoryIndex(nextIndex);
    setDraft(nextDraft);
    persist(nextDraft);
  }

  function move(index: number, direction: -1 | 1) {
    if (!draft) return;

    const destination = index + direction;

    if (
      destination < 0 ||
      destination >= draft.sectionOrder.length
    ) {
      return;
    }

    const nextOrder = [...draft.sectionOrder];

    [nextOrder[index], nextOrder[destination]] = [
      nextOrder[destination],
      nextOrder[index],
    ];

    change({
      ...draft,
      sectionOrder: nextOrder,
    });
  }

  function toggle(section: StudioSection) {
    if (!draft) return;

    change({
      ...draft,
      hiddenSections: draft.hiddenSections.includes(section)
        ? draft.hiddenSections.filter(
            (item) => item !== section,
          )
        : [...draft.hiddenSections, section],
    });
  }

  async function exportDocument(format: "pdf" | "docx") {
    if (!draft) return;

    setError("");

    try {
      const blob = await api<Blob>(
        `/api/ai-cv/export/${format}`,
        {
          method: "POST",
          body: JSON.stringify(buildExportPayload(draft)),
        },
      );

      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");

      anchor.href = url;
      anchor.download = `${draft.cvTitle
        .replace(/[^a-z0-9]+/gi, "-")
        .toLowerCase()}.${format}`;

      anchor.click();
      URL.revokeObjectURL(url);
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Export failed",
      );
    }
  }

  useEffect(() => {
    function handleKeyboard(event: KeyboardEvent) {
      if (
        event.ctrlKey &&
        event.key.toLowerCase() === "s"
      ) {
        event.preventDefault();

        if (draft) {
          localStorage.setItem(
            STUDIO_DRAFT_KEY,
            JSON.stringify(draft),
          );
          setSaveState("saved");
        }
      }

      if (
        event.ctrlKey &&
        event.key.toLowerCase() === "z"
      ) {
        event.preventDefault();
        undo();
      }

      if (
        event.ctrlKey &&
        event.key.toLowerCase() === "y"
      ) {
        event.preventDefault();
        redo();
      }
    }

    window.addEventListener("keydown", handleKeyboard);

    return () =>
      window.removeEventListener(
        "keydown",
        handleKeyboard,
      );
  });

  if (error) {
    return <div className="error">{error}</div>;
  }

  if (!draft) {
    return (
      <div className="loading">
        <span className="spinner" />
        Opening CV Studio...
      </div>
    );
  }

  return (
    <div
      className={`cv-studio-shell ${
        preview ? "preview-only" : ""
      }`}
    >
      <Toolbar
        saveState={saveState}
        canUndo={historyIndex > 0}
        canRedo={historyIndex < history.length - 1}
        onUndo={undo}
        onRedo={redo}
        onSave={() => {
          localStorage.setItem(
            STUDIO_DRAFT_KEY,
            JSON.stringify(draft),
          );
          setSaveState("saved");
        }}
        onExportPDF={() => exportDocument("pdf")}
        onExportDOCX={() => exportDocument("docx")}
        previewOnly={preview}
        setPreviewOnly={setPreview}
      />

      {!preview && (
        <div className="studio-mode-tabs">
          <button
            className={mode === "content" ? "active" : ""}
            onClick={() => setMode("content")}
          >
            Content
          </button>

          <button
            className={mode === "design" ? "active" : ""}
            onClick={() => setMode("design")}
          >
            Design
          </button>
        </div>
      )}

      <div className="cv-studio-workspace">
        {!preview && mode === "content" && (
          <SectionSidebar
            draft={draft}
            active={active}
            onSelect={setActive}
            onMove={move}
            onToggle={toggle}
          />
        )}

        {!preview && mode === "content" && (
          <EditorPanel
            draft={draft}
            active={active}
            onChange={change}
          />
        )}

        {!preview && mode === "design" && (
          <div className="studio-design-spacer" />
        )}

        {!preview && mode === "design" && (
          <DesignPanel
            draft={draft}
            onChange={change}
          />
        )}

        <PreviewPanel
          draft={draft}
          zoom={zoom}
          setZoom={setZoom}
        />
      </div>
    </div>
  );
}
