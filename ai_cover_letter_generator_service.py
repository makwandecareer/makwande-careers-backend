from __future__ import annotations

from typing import Any


class AICoverLetterGeneratorService:
    """
    Generates ATS-friendly cover letters.
    Replace the template builder with an LLM call when AI integration
    is enabled.
    """

    def generate(
        self,
        profile: dict[str, Any],
        company_name: str,
        job_title: str,
        job_description: str = "",
    ) -> dict[str, Any]:

        name = profile.get("full_name", "Candidate")
        intro = (
            f"Dear Hiring Manager,\n\n"
            f"I am writing to express my interest in the {job_title} position "
            f"at {company_name}. My background, skills, and experience align "
            f"well with the requirements of this opportunity."
        )

        body = (
            f"\n\nThroughout my career I have demonstrated strong problem-solving, "
            f"leadership, communication, and technical capabilities while "
            f"delivering measurable results. I am confident that I can make "
            f"a positive contribution to {company_name}."
        )

        if job_description:
            body += (
                "\n\nI have carefully reviewed the job requirements and "
                "believe my experience aligns with the key responsibilities "
                "and competencies outlined for this role."
            )

        closing = (
            "\n\nThank you for considering my application. I welcome the "
            "opportunity to discuss how my experience and skills can support "
            "your team.\n\nYours sincerely,\n"
            f"{name}"
        )

        return {
            "cover_letter": intro + body + closing,
            "metadata": {
                "candidate": name,
                "company": company_name,
                "job_title": job_title,
            },
            "recommendations": [
                "Address the hiring manager by name when possible.",
                "Customize the letter for every application.",
                "Support claims with measurable achievements.",
                "Keep the cover letter to one page."
            ],
            "ai_ready": True,
        }
