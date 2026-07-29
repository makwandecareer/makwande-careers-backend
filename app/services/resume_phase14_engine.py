from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.services.resume_formalization_engine import formalize_resume_content
from app.services.resume_skills_engine import classify_skills
from app.services.resume_intelligence_engine import analyse_resume

DEFAULT_DECLARATION = (
    "I hereby declare that the information provided in this Curriculum Vitae is true and accurate "
    "to the best of my knowledge. I consent to prospective employers processing my personal "
    "information for legitimate recruitment purposes in accordance with applicable privacy "
    "legislation, including the Protection of Personal Information Act (POPIA), where applicable."
)


def enrich_phase14(content: dict[str, Any], job_description: str = "") -> tuple[dict[str, Any], dict[str, Any]]:
    result = deepcopy(content or {})
    result = formalize_resume_content(result)
    result = classify_skills(result)

    if not result.get("references"):
        result["references"] = "Available upon request."
    if not result.get("declaration"):
        result["declaration"] = DEFAULT_DECLARATION

    intelligence = analyse_resume(result, job_description)
    result["resume_intelligence"] = intelligence
    return result, intelligence
