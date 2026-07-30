from __future__ import annotations

from typing import Any


class TemplateRenderer:
    """
    Shared renderer for PDF and DOCX exports.

    Converts a CV Studio draft into a normalized render model
    so every export format uses the same data.
    """

    def _content(self, draft: dict[str, Any]) -> dict[str, Any]:
        """
        Extract the CV content regardless of whether the payload
        is the full export payload or just the draft itself.
        """
        if isinstance(draft, dict) and "cv_content" in draft:
            return draft["cv_content"]

        return draft

    def _metadata(self, draft: dict[str, Any]) -> dict[str, Any]:
        content = self._content(draft)
        personal = content.get("personal_details", {})

        return {
            "title": personal.get("full_name", "Curriculum Vitae"),
            "template": draft.get("template_key", ""),
            "design": draft.get("design", {}),
        }

    def build_pdf(self, draft: dict[str, Any]) -> dict[str, Any]:
        content = self._content(draft)

        return {
            "metadata": self._metadata(draft),
            "summary": content.get("professional_summary", ""),
            "experience": content.get("experience", []),
            "education": content.get("education", []),
            "skills": content.get("skills", []),
            "projects": content.get("projects", []),
            "certifications": content.get("certifications", []),
            "references": content.get("references", ""),
        }

    def build_docx(self, draft: dict[str, Any]) -> dict[str, Any]:
        """
        DOCX currently uses the same render model as PDF.
        """
        return self.build_pdf(draft)