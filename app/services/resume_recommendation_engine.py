from __future__ import annotations

import re
from datetime import date
from typing import Any


DEFAULT_POPIA_DECLARATION = (
    "I consent to prospective employers processing the personal information "
    "contained in this CV for legitimate recruitment and employment purposes, "
    "subject to the Protection of Personal Information Act, 2013 (POPIA)."
)

MONTH_YEAR_PATTERN = re.compile(
    r"^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.\d{4}$",
    re.IGNORECASE,
)


def _record(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _items(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _has_metric(value: str) -> bool:
    return bool(
        re.search(
            r"(?:\b\d+(?:\.\d+)?%|\bR\s?\d|\b\d+\s*(?:patients|prescriptions|"
            r"audits|wards|clinics|staff|reports|cases|orders|units|sites|"
            r"branches|projects|days|hours|months|years)\b)",
            value,
            re.IGNORECASE,
        )
    )


def _format_date(value: Any) -> str:
    text = _text(value)
    if not text:
        return ""

    if MONTH_YEAR_PATTERN.match(text):
        return text

    try:
        parsed = date.fromisoformat(text[:10])
        return parsed.strftime("%b.%Y")
    except ValueError:
        return text


def _normalise_dates(entries: list[Any]) -> list[Any]:
    result: list[Any] = []

    for entry in entries:
        if not isinstance(entry, dict):
            result.append(entry)
            continue

        item = dict(entry)
        item["start_date"] = _format_date(item.get("start_date"))

        is_current = bool(
            item.get("is_current")
            or item.get("current")
            or _text(item.get("end_date")).lower() in {"present", "current"}
        )
        item["end_date"] = (
            "Present" if is_current else _format_date(item.get("end_date"))
        )
        result.append(item)

    return result


def _profile_score(content: dict[str, Any]) -> int:
    personal = _record(content.get("personal_details"))

    checks = [
        bool(_text(personal.get("full_name"))),
        bool(_text(personal.get("email"))),
        bool(_text(personal.get("phone"))),
        bool(_text(personal.get("location"))),
        bool(_text(content.get("professional_title"))),
        bool(_text(content.get("professional_summary"))),
        bool(_items(content.get("skills"))),
        bool(_items(content.get("experience"))),
        bool(_items(content.get("education"))),
        bool(_items(content.get("certifications"))),
    ]

    return round((sum(checks) / len(checks)) * 100)


def enrich_resume_content(
    cv_content: dict[str, Any],
    *,
    target_role: str = "",
) -> tuple[dict[str, Any], list[dict[str, str]], int]:
    """
    Add safe resume standards and return user-facing recommendations.

    The engine never invents employment dates, metrics, qualifications,
    memberships, licences, LinkedIn URLs, or achievements.
    """

    content = dict(cv_content or {})
    personal = _record(content.get("personal_details"))
    experience = _normalise_dates(_items(content.get("experience")))
    education = _normalise_dates(_items(content.get("education")))

    content["personal_details"] = personal
    content["experience"] = experience
    content["education"] = education
    content["professional_title"] = (
        _text(content.get("professional_title"))
        or _text(target_role)
    )
    content["references"] = (
        content.get("references")
        or "Available upon request"
    )
    content["declaration"] = (
        _text(content.get("declaration"))
        or DEFAULT_POPIA_DECLARATION
    )

    recommendations: list[dict[str, str]] = []

    def add(
        code: str,
        title: str,
        message: str,
        action: str,
        severity: str = "medium",
    ) -> None:
        recommendations.append(
            {
                "code": code,
                "title": title,
                "message": message,
                "action": action,
                "severity": severity,
            }
        )

    if not _text(personal.get("linkedin_url")):
        add(
            "missing_linkedin",
            "Add a LinkedIn profile",
            "A verified LinkedIn URL improves recruiter confidence and profile discoverability.",
            "Add the candidate's correct LinkedIn profile URL.",
        )

    summary = _text(content.get("professional_summary"))
    if len(summary.split()) < 35:
        add(
            "weak_summary",
            "Strengthen the professional summary",
            "Use 45–80 words covering career level, sector exposure, strongest technical areas and verified value.",
            "Improve the summary without inventing claims.",
            "high",
        )

    if experience:
        for index, item in enumerate(experience, start=1):
            if not isinstance(item, dict):
                continue

            role = (
                _text(item.get("job_title"))
                or _text(item.get("title"))
                or f"Position {index}"
            )
            description = _text(item.get("description"))
            achievements = [
                _text(value)
                for value in _items(item.get("achievements"))
                if _text(value)
            ]
            combined = " ".join([description, *achievements])

            if not _text(item.get("start_date")):
                add(
                    f"missing_start_date_{index}",
                    f"Add the start date for {role}",
                    "Recruiters and ATS systems expect employment dates.",
                    "Use the verified format (Mon.YYYY) – (Mon.YYYY) or Present.",
                    "high",
                )

            if not _text(item.get("end_date")):
                add(
                    f"missing_end_date_{index}",
                    f"Add the end date for {role}",
                    "The duration of employment is incomplete.",
                    "Add a verified end date or mark the role as Present.",
                    "high",
                )

            if not achievements:
                add(
                    f"missing_achievements_{index}",
                    f"Add achievements for {role}",
                    "The role currently describes duties but does not show evidence of impact.",
                    "Add two to four verified achievement bullets.",
                    "high",
                )
            elif not _has_metric(combined):
                add(
                    f"missing_kpis_{index}",
                    f"Add measurable evidence for {role}",
                    "No verified KPI, quantity, turnaround time, quality result or operational scope was detected.",
                    "Ask the candidate for real numbers and add only verified metrics.",
                )

    skills = _items(content.get("skills"))
    technical_terms = {
        "dispensing",
        "stock management",
        "quality assurance",
        "cgmp",
        "bmr",
        "bpr",
        "sop",
        "deviation investigation",
        "change control",
        "pharmaceutical care",
    }
    skill_names = {
        _text(item.get("name") if isinstance(item, dict) else item).lower()
        for item in skills
    }
    if skills and not (skill_names & technical_terms):
        add(
            "technical_skills",
            "Separate technical competencies",
            "Recruiters should quickly see profession-specific tools, systems and regulated-practice skills.",
            "Create a Technical Skills section using verified candidate information.",
        )

    memberships = _items(content.get("professional_memberships"))
    if not memberships:
        add(
            "professional_memberships",
            "Confirm professional registrations",
            "Regulated professions should clearly show active councils, boards, licence numbers and registration status.",
            "Add verified professional memberships or registrations, including expiry dates where applicable.",
            "high",
        )

    if not _items(content.get("certifications")):
        add(
            "certifications",
            "Add verified certifications",
            "Relevant licences and training improve recruiter screening.",
            "Add certification name, issuing body and verified issue or expiry date.",
        )

    if not _text(content.get("declaration")):
        add(
            "popia",
            "Add POPIA consent",
            "The CV should include candidate consent for legitimate recruitment processing.",
            "Insert the standard POPIA declaration.",
        )

    if not content.get("references"):
        add(
            "references",
            "Add a references statement",
            "A clear references statement completes the document.",
            "Use 'Available upon request' unless verified referees are supplied.",
            "low",
        )

    score = _profile_score(content)
    return content, recommendations, score
