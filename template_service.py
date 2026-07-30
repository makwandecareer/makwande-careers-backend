from __future__ import annotations

from copy import deepcopy

DEFAULT_TEMPLATE = "modern"

TEMPLATES = {
    "modern": {
        "layout": "modern",
        "font": "Inter",
        "primary_color": "#0F766E",
        "secondary_color": "#E6FFFA",
    },
    "professional": {
        "layout": "professional",
        "font": "Calibri",
        "primary_color": "#1F2937",
        "secondary_color": "#F3F4F6",
    },
    "executive": {
        "layout": "executive",
        "font": "Georgia",
        "primary_color": "#111827",
        "secondary_color": "#F9FAFB",
    },
}


class TemplateService:
    """
    Central template engine.
    The same template configuration should be used for
    preview, PDF export and DOCX export.
    """

    def list_templates(self) -> list[str]:
        return sorted(TEMPLATES.keys())

    def get_template(self, template_id: str) -> dict:
        if template_id not in TEMPLATES:
            template_id = DEFAULT_TEMPLATE
        return deepcopy(TEMPLATES[template_id])

    def apply_template(self, draft) -> dict:
        template = self.get_template(draft.template_id)
        return {
            "template": template,
            "draft": draft,
        }

    def build_export_payload(self, draft) -> dict:
        """
        Always use the same renderer payload for Preview,
        PDF and DOCX to avoid template mismatches.
        """
        return self.apply_template(draft)
