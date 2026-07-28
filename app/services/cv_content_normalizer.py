from __future__ import annotations

from typing import Any


def _record(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value

    return {}


def _list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value

    return []


def _text(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()

    return ""


def normalise_cv_content(
    cv_content: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Convert every supported frontend CV shape into one canonical structure.

    Supports:
    - profile source-of-truth bundles
    - imported CV drafts
    - generated CV snapshots
    - direct CV editor payloads
    """

    content = dict(cv_content or {})

    user = _record(content.get("user"))
    profile = _record(content.get("profile"))
    personal = _record(content.get("personal_details"))

    personal_details = {
        "full_name": _text(
            personal.get("full_name"),
            user.get("full_name"),
            content.get("full_name"),
        ),
        "email": _text(
            personal.get("email"),
            user.get("email"),
            content.get("email"),
        ),
        "phone": _text(
            personal.get("phone"),
            profile.get("phone"),
            content.get("phone"),
        ),
        "location": _text(
            personal.get("location"),
            profile.get("location"),
            content.get("location"),
        ),
        "linkedin_url": _text(
            personal.get("linkedin_url"),
            profile.get("linkedin_url"),
            content.get("linkedin_url"),
        ),
        "portfolio_url": _text(
            personal.get("portfolio_url"),
            profile.get("portfolio_url"),
            content.get("portfolio_url"),
        ),
        "website_url": _text(
            personal.get("website_url"),
            profile.get("website_url"),
            content.get("website_url"),
        ),
    }

    references = content.get("references")

    if not references:
        references = "Available upon request"

    declaration = _text(
        content.get("declaration"),
        (
            "I consent to prospective employers processing the personal "
            "information contained in this CV for legitimate recruitment "
            "and employment purposes, subject to applicable "
            "data-protection legislation."
        ),
    )

    normalised = {
        **content,
        "personal_details": personal_details,
        "professional_title": _text(
            content.get("professional_title"),
            content.get("target_role"),
            profile.get("professional_title"),
        ),
        "professional_summary": _text(
            content.get("professional_summary"),
            profile.get("professional_summary"),
        ),
        "skills": _list(content.get("skills")),
        "experience": _list(content.get("experience")),
        "education": _list(content.get("education")),
        "projects": _list(content.get("projects")),
        "certifications": _list(content.get("certifications")),
        "languages": _list(content.get("languages")),
        "references": references,
        "declaration": declaration,
    }

    return normalised