from __future__ import annotations

from copy import deepcopy
from typing import Any

STANDARD_TERMS = {
    "gmp", "glp", "haccp", "fssc 22000", "iso 9001", "iso 22000",
    "ohsas", "food safety", "quality standards", "health and safety",
}
SOFTWARE_TERMS = {
    "sap", "erp", "mes", "microsoft office", "excel", "power bi", "oracle",
    "salesforce", "sql", "python", "laboratory information management system",
}
EQUIPMENT_TERMS = {
    "hplc", "spectrophotometer", "ph meter", "laboratory equipment",
    "production machinery", "microbiology equipment", "calibration equipment",
}
PROFESSIONAL_TERMS = {
    "communication", "team collaboration", "leadership", "problem solving",
    "time management", "stakeholder engagement", "attention to detail",
    "continuous improvement", "decision making", "adaptability",
}


def _text(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("name") or value.get("skill") or value.get("title")
    return " ".join(str(value or "").strip().split())


def classify_skills(content: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(content or {})
    source = result.get("skills") or []
    names: list[str] = []
    for value in source:
        name = _text(value)
        if name and name.casefold() not in {item.casefold() for item in names}:
            names.append(name)

    categories: dict[str, list[str]] = {
        "technical_skills": [],
        "software_and_systems": [],
        "laboratory_and_equipment": [],
        "industry_standards": [],
        "professional_competencies": [],
    }

    for name in names:
        lower = name.casefold()
        if lower in STANDARD_TERMS or any(term in lower for term in STANDARD_TERMS):
            categories["industry_standards"].append(name)
        elif lower in SOFTWARE_TERMS or any(term in lower for term in SOFTWARE_TERMS):
            categories["software_and_systems"].append(name)
        elif lower in EQUIPMENT_TERMS or any(term in lower for term in EQUIPMENT_TERMS):
            categories["laboratory_and_equipment"].append(name)
        elif lower in PROFESSIONAL_TERMS or any(term in lower for term in PROFESSIONAL_TERMS):
            categories["professional_competencies"].append(name)
        else:
            categories["technical_skills"].append(name)

    result["skill_categories"] = categories
    return result
