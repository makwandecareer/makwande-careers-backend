from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.services.template_service import TemplateService


class TemplateRenderer:
    """
    Converts a CV draft into a single normalized render model.
    The same render model must be used by:
      - Live Preview
      - PDF Export
      - DOCX Export
    """

    def __init__(self):
        self.templates = TemplateService()

    def render(self, draft) -> dict[str, Any]:
        template = self.templates.get_template(draft.template_id)

        return {
            "template": deepcopy(template),
            "profile": deepcopy(draft.profile),
            "summary": draft.summary,
            "experience": deepcopy(draft.experience),
            "education": deepcopy(draft.education),
            "skills": deepcopy(draft.skills),
            "certifications": deepcopy(draft.certifications),
            "projects": deepcopy(draft.projects),
            "languages": deepcopy(draft.languages),
            "references": deepcopy(draft.references),
            "design": deepcopy(draft.design),
            "metadata": {
                "draft_id": str(draft.id),
                "title": draft.title,
                "version": draft.version,
            },
        }

    def build_preview(self, draft) -> dict[str, Any]:
        return self.render(draft)

    def build_pdf(self, draft) -> dict[str, Any]:
        return self.render(draft)

    def build_docx(self, draft) -> dict[str, Any]:
        return self.render(draft)
