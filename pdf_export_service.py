from __future__ import annotations

from io import BytesIO

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate

from app.services.template_renderer import TemplateRenderer


class PDFExportService:
    """
    Production PDF export service.
    Uses the same render model as the live preview.
    """

    def __init__(self):
        self.renderer = TemplateRenderer()

    def export(self, draft) -> bytes:
        model = self.renderer.build_pdf(draft)

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer)
        styles = getSampleStyleSheet()

        story = [
            Paragraph(f"<b>{model['metadata']['title']}</b>", styles["Title"]),
            Paragraph(model["summary"] or "", styles["BodyText"]),
        ]

        for job in model["experience"]:
            story.append(
                Paragraph(
                    f"<b>{job.get('position','')}</b> - {job.get('company','')}",
                    styles["Heading2"],
                )
            )
            story.append(
                Paragraph(job.get("description", ""), styles["BodyText"])
            )

        doc.build(story)
        return buffer.getvalue()
