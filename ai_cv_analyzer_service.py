from __future__ import annotations

from typing import Any


class AICVAnalyzerService:
    """
    AI-ready CV analysis service.
    This version provides the analysis pipeline; an LLM provider
    can later be plugged into generate_ai_feedback().
    """

    REQUIRED_SECTIONS = [
        "profile",
        "summary",
        "experience",
        "education",
        "skills",
    ]

    def analyse(self, draft) -> dict[str, Any]:
        missing = self._missing_sections(draft)
        score = self._score(draft, missing)

        return {
            "ats_score": score,
            "missing_sections": missing,
            "strengths": self._strengths(draft),
            "weaknesses": self._weaknesses(draft, missing),
            "recommendations": self._recommendations(draft, missing),
            "ai_feedback": self.generate_ai_feedback(draft),
        }

    def _missing_sections(self, draft) -> list[str]:
        missing = []
        for section in self.REQUIRED_SECTIONS:
            value = getattr(draft, section, None)
            if not value:
                missing.append(section)
        return missing

    def _score(self, draft, missing) -> int:
        score = 100 - len(missing) * 10
        if getattr(draft, "summary", ""):
            score += 5
        if getattr(draft, "experience", []):
            score += 5
        return max(0, min(100, score))

    def _strengths(self, draft) -> list[str]:
        s = []
        if getattr(draft, "experience", None):
            s.append("Professional experience included.")
        if getattr(draft, "skills", None):
            s.append("Skills section present.")
        return s

    def _weaknesses(self, draft, missing) -> list[str]:
        return [f"Missing {m} section." for m in missing]

    def _recommendations(self, draft, missing) -> list[str]:
        rec = []
        if "summary" in missing:
            rec.append("Add a professional summary.")
        rec.append("Use measurable achievements with KPIs.")
        rec.append("Tailor keywords to the target job description.")
        rec.append("Keep dates and formatting ATS compliant.")
        return rec

    def generate_ai_feedback(self, draft) -> str:
        return (
            "AI integration placeholder: connect your preferred LLM "
            "to produce detailed CV analysis and rewrite suggestions."
        )
