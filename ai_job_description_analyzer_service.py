from __future__ import annotations

import re
from collections import Counter
from typing import Any


class AIJobDescriptionAnalyzerService:
    """
    Compares a CV against a job description and produces
    ATS-oriented recommendations.
    """

    STOP_WORDS = {
        "the","and","for","with","from","that","this","will","your","you",
        "our","are","have","has","into","their","they","about","using","able"
    }

    def analyze(
        self,
        job_description: str,
        cv_text: str,
    ) -> dict[str, Any]:

        jd_keywords = self._extract_keywords(job_description)
        cv_keywords = self._extract_keywords(cv_text)

        matched = sorted(jd_keywords & cv_keywords)
        missing = sorted(jd_keywords - cv_keywords)

        score = round((len(matched) / max(1, len(jd_keywords))) * 100)

        return {
            "match_score": score,
            "job_keywords": sorted(jd_keywords),
            "matched_keywords": matched,
            "missing_keywords": missing,
            "recommendations": self._recommendations(score, missing),
            "ai_ready": True,
        }

    def _extract_keywords(self, text: str) -> set[str]:
        words = re.findall(r"[A-Za-z][A-Za-z0-9\-\+\.#]*", text.lower())
        counts = Counter(
            w for w in words
            if len(w) > 2 and w not in self.STOP_WORDS
        )
        return {word for word, _ in counts.most_common(100)}

    def _recommendations(self, score: int, missing: list[str]) -> list[str]:
        rec = []
        if score < 70:
            rec.append("Increase alignment between your CV and the job description.")
        if missing:
            rec.append("Include relevant missing keywords where they accurately reflect your experience.")
        rec.append("Tailor your professional summary to the target role.")
        rec.append("Quantify achievements using measurable KPIs.")
        rec.append("Keep wording truthful and ATS-friendly.")
        return rec
