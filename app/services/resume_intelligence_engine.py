from __future__ import annotations

import re
from collections import Counter
from typing import Any

STOPWORDS = {
    "and", "the", "with", "for", "that", "this", "from", "are", "was", "were",
    "have", "has", "will", "your", "you", "our", "their", "they", "into", "using",
    "a", "an", "of", "to", "in", "on", "at", "as", "or", "be", "is", "it",
}


def _flatten(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(_flatten(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return " ".join(_flatten(v) for v in value)
    return "" if value is None else str(value)


def _words(text: str) -> list[str]:
    values = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]{1,}", text.lower())
    return [value for value in values if value not in STOPWORDS and len(value) > 2]


def _has_metric(text: str) -> bool:
    return bool(re.search(r"\b\d+(?:\.\d+)?\s*(?:%|percent|days?|hours?|months?|years?|units?|cases?|projects?|people|staff|clients?|customers?|audits?)?\b", text, re.I))


def analyse_resume(content: dict[str, Any], job_description: str = "") -> dict[str, Any]:
    text = _flatten(content)
    job_words = [word for word, _ in Counter(_words(job_description)).most_common(40)]
    cv_words = set(_words(text))
    matched = [word for word in job_words if word in cv_words]
    missing = [word for word in job_words if word not in cv_words]

    section_fields = (
        "professional_summary", "skills", "experience", "education",
        "certifications", "professional_memberships", "references", "declaration",
    )
    present = sum(1 for field in section_fields if content.get(field))
    completeness = round((present / len(section_fields)) * 100)

    experience = content.get("experience") or []
    responsibilities = sum(
        len(item.get("responsibilities") or item.get("duties") or [])
        for item in experience if isinstance(item, dict)
    )
    achievements = [
        value for item in experience if isinstance(item, dict)
        for value in (item.get("achievements") or [])
    ]
    metric_count = sum(1 for value in achievements if _has_metric(str(value)))

    keyword_match = round((len(matched) / max(len(job_words), 1)) * 100) if job_words else 0
    formatting_score = 100 if responsibilities or not experience else 65
    achievement_score = min(100, 45 + metric_count * 15) if achievements else 35
    recruiter_readiness = round(
        completeness * 0.45 + formatting_score * 0.25 + achievement_score * 0.15 + (keyword_match or completeness) * 0.15
    )
    ats_score = round(keyword_match * 0.65 + completeness * 0.35) if job_words else completeness

    warnings: list[str] = []
    if experience and not responsibilities:
        warnings.append("Convert work duties into clear point-form responsibilities.")
    if not achievements:
        warnings.append("Add verified achievements; do not invent figures.")
    elif not metric_count:
        warnings.append("Add verified KPI evidence to achievements where available.")
    if not (content.get("personal_details") or {}).get("linkedin_url"):
        warnings.append("Add a verified LinkedIn profile URL.")

    return {
        "ats_score": min(100, ats_score),
        "profile_readiness": min(100, completeness),
        "recruiter_readiness": min(100, recruiter_readiness),
        "formatting_score": formatting_score,
        "keyword_match": keyword_match,
        "matched_keywords": matched,
        "missing_keywords": missing[:25],
        "responsibility_bullet_count": responsibilities,
        "achievement_count": len(achievements),
        "measurable_achievement_count": metric_count,
        "warnings": warnings,
        "disclaimer": "Scores are AI-assisted guidance based only on supplied CV content and any supplied job description; they are not hiring guarantees.",
    }
