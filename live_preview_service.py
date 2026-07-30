from __future__ import annotations

from typing import Any

from app.services.template_renderer import TemplateRenderer


class LivePreviewService:
    """
    Builds the live preview model used by the frontend.
    The output is identical to the model used for PDF and DOCX exports.
    """

    def __init__(self):
        self.renderer = TemplateRenderer()

    def build(self, draft) -> dict[str, Any]:
        model = self.renderer.build_preview(draft)
        return {
            "template": model["template"],
            "design": model["design"],
            "metadata": model["metadata"],
            "sections": {
                "profile": model["profile"],
                "summary": model["summary"],
                "experience": model["experience"],
                "education": model["education"],
                "skills": model["skills"],
                "certifications": model["certifications"],
                "projects": model["projects"],
                "languages": model["languages"],
                "references": model["references"],
            },
        }

    def refresh(self, draft) -> dict[str, Any]:
        return self.build(draft)

    def autosave_preview(self, draft) -> dict[str, Any]:
        return self.build(draft)
