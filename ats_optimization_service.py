from __future__ import annotations

from collections import Counter
from typing import Any


DEFAULT_KEYWORDS = {
    "leadership","management","communication","planning","analysis",
    "problem solving","teamwork","safety","quality","project",
    "budget","compliance","reporting","customer","operations",
}


class ATSOptimizationService:
    """
    Basic ATS optimisation engine.
    Produces a score and recommendations before export.
    """

    def analyse(self, draft) -> dict[str, Any]:
        text = self._collect_text(draft).lower()

        matched = [k for k in DEFAULT_KEYWORDS if k in text]
        missing = sorted(DEFAULT_KEYWORDS.difference(matched))

        score = min(100, 40 + len(matched) * 6)

        return {
            "score": score,
            "matched_keywords": sorted(matched),
            "missing_keywords": missing,
            "recommendations": self._recommend(score, missing),
            "word_frequency": Counter(text.split()).most_common(25),
        }

    def _collect_text(self, draft) -> str:
        parts = [
            getattr(draft, "summary", "") or "",
            str(getattr(draft, "experience", "")),
            str(getattr(draft, "education", "")),
            str(getattr(draft, "skills", "")),
            str(getattr(draft, "projects", "")),
        ]
        return " ".join(parts)

    def _recommend(self, score: int, missing: list[str]) -> list[str]:
        rec = []
        if score < 80:
            rec.append("Increase ATS keyword coverage.")
        if missing:
            rec.append("Include role-specific keywords from the job description.")
        rec.append("Use measurable achievements with KPIs.")
        rec.append("Use standard section headings.")
        rec.append("Keep formatting simple and ATS compatible.")
        return rec
