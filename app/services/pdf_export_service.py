from __future__ import annotations

from io import BytesIO

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from app.services.template_renderer import TemplateRenderer


class PDFExportService:
    """
    Export a CV Studio draft to PDF.
    """

    def __init__(self):
        self.renderer = TemplateRenderer()

    def export(self, draft: dict) -> bytes:
        data = self.renderer.build_pdf(draft)

        buffer = BytesIO()

        doc = SimpleDocTemplate(buffer)

        styles = getSampleStyleSheet()

        story = []

        metadata = data["metadata"]

        story.append(Paragraph(metadata["title"], styles["Title"]))
        story.append(Spacer(1, 12))

        summary = data.get("summary")
        if summary:
            story.append(Paragraph("<b>Professional Summary</b>", styles["Heading2"]))
            story.append(Paragraph(summary, styles["BodyText"]))
            story.append(Spacer(1, 12))

        if data["experience"]:
            story.append(Paragraph("<b>Experience</b>", styles["Heading2"]))

            for item in data["experience"]:
                title = item.get("job_title", "")
                company = item.get("company", "")
                period = item.get("duration", "")

                story.append(
                    Paragraph(
                        f"<b>{title}</b> — {company} ({period})",
                        styles["BodyText"],
                    )
                )

                for duty in item.get("responsibilities", []):
                    story.append(
                        Paragraph(f"• {duty}", styles["BodyText"])
                    )

                story.append(Spacer(1, 8))

        if data["education"]:
            story.append(Paragraph("<b>Education</b>", styles["Heading2"]))

            for item in data["education"]:
                story.append(
                    Paragraph(
                        f"{item.get('qualification','')} - {item.get('institution','')}",
                        styles["BodyText"],
                    )
                )

            story.append(Spacer(1, 12))

        if data["skills"]:
            story.append(Paragraph("<b>Skills</b>", styles["Heading2"]))

            skills = ", ".join(data["skills"])

            story.append(
                Paragraph(skills, styles["BodyText"])
            )

        doc.build(story)

        pdf = buffer.getvalue()

        buffer.close()

        return pdf