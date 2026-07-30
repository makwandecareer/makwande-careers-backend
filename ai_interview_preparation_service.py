from __future__ import annotations

from typing import Any


class AIInterviewPreparationService:
    """
    Generates interview preparation content.
    AI-ready: replace placeholder generation with an LLM provider.
    """

    BEHAVIORAL = [
        "Tell me about yourself.",
        "Describe a time you solved a difficult problem.",
        "Tell me about a conflict you handled.",
        "Describe a successful project you delivered."
    ]

    def generate(
        self,
        profile: dict[str, Any],
        job_title: str,
        industry: str | None = None,
        skills: list[str] | None = None,
    ) -> dict[str, Any]:
        skills = skills or []

        technical = [
            f"Explain your experience related to {s}."
            for s in skills[:5]
        ]

        model_answers = {
            q: "Use the STAR method (Situation, Task, Action, Result) and support your answer with measurable outcomes."
            for q in (self.BEHAVIORAL + technical)
        }

        tips = [
            "Research the company before the interview.",
            "Use the STAR method for behavioural questions.",
            "Quantify your achievements with KPIs where possible.",
            "Prepare thoughtful questions for the interviewer.",
            "Review the job description and align your examples."
        ]

        return {
            "candidate": profile.get("full_name", "Candidate"),
            "job_title": job_title,
            "industry": industry,
            "behavioral_questions": self.BEHAVIORAL,
            "technical_questions": technical,
            "model_answers": model_answers,
            "interview_tips": tips,
            "checklist": [
                "Bring updated copies of your CV.",
                "Arrive 10–15 minutes early.",
                "Dress appropriately for the role.",
                "Test your camera and microphone for virtual interviews."
            ],
            "ai_ready": True,
        }
