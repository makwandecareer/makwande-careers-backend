import type { StudioDraft } from "@/lib/cv-studio";
import type { RealTemplate } from "@/lib/real-template-catalog";

export const SELECTED_TEMPLATE_KEY = "makwande_cv_template";
export const STUDIO_DRAFT_KEY = "makwande_cv_studio_draft_v1";

function mapHeaderStyle(
  template: RealTemplate,
): StudioDraft["headerStyle"] {
  switch (template.layout) {
    case "centered":
      return "centered";
    case "top-band":
    case "split-header":
      return "banded";
    case "minimal-line":
      return "minimal";
    default:
      return "classic";
  }
}

function mapLayout(
  template: RealTemplate,
): StudioDraft["layout"] {
  return template.columns === 2 ? "two-column" : "one-column";
}

export function applyTemplateToDraft(
  draft: StudioDraft,
  template: RealTemplate,
): StudioDraft {
  return {
    ...draft,
    templateKey: template.key,
    templateLayout: template.layout,
    templateName: template.name,
    layout: mapLayout(template),
    headerStyle: mapHeaderStyle(template),
    accent: template.palette[1] || draft.accent,
    secondaryAccent: template.palette[0] || draft.secondaryAccent,
    fontFamily: template.font || draft.fontFamily,
    headingFont: template.font || draft.headingFont,
    showPhoto: template.photo === "with-photo",
  };
}

export function readSelectedTemplate(): RealTemplate | null {
  if (typeof window === "undefined") return null;

  const raw = window.localStorage.getItem(SELECTED_TEMPLATE_KEY);

  if (!raw) return null;

  try {
    return JSON.parse(raw) as RealTemplate;
  } catch {
    window.localStorage.removeItem(SELECTED_TEMPLATE_KEY);
    return null;
  }
}

export function saveSelectedTemplate(template: RealTemplate): void {
  window.localStorage.setItem(
    SELECTED_TEMPLATE_KEY,
    JSON.stringify(template),
  );
}

export function buildExportPayload(draft: StudioDraft) {
  return {
    filename: draft.cvTitle,
    template_key: draft.templateKey,
    template_name: draft.templateName || "",
    template_layout: draft.templateLayout || "",
    design: {
      layout: draft.layout,
      header_style: draft.headerStyle,
      accent: draft.accent,
      secondary_accent: draft.secondaryAccent,
      font_family: draft.fontFamily,
      heading_font: draft.headingFont,
      font_size: draft.fontSize,
      line_height: draft.lineHeight,
      section_spacing: draft.sectionSpacing,
      margin: draft.margin,
      show_photo: draft.showPhoto,
      photo_shape: draft.photoShape,
    },
    cv_content: draft,
  };
}
