from __future__ import annotations

import re
from copy import deepcopy
from typing import Any, Iterable

_ACTION_REPLACEMENTS = {
    "responsible for": "Managed",
    "helped": "Supported",
    "worked on": "Contributed to",
    "did": "Performed",
    "handled": "Managed",
    "made sure": "Ensured",
    "checked": "Verified",
    "checking": "Conducted",
    "ran": "Operated",
    "running": "Operated",
    "looked after": "Maintained",
    "dealt with": "Managed",
}


def _text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _items(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, str):
        # Split only where the source clearly contains separate duties.
        parts = re.split(r"(?:\r?\n|\s*[;•]\s*)", value)
        return [part for part in parts if _text(part)]
    return [value]


def _sentence(value: Any) -> str:
    text = _text(value).lstrip("-• ")
    if not text:
        return ""
    lowered = text.lower()
    for weak, strong in _ACTION_REPLACEMENTS.items():
        if lowered.startswith(weak):
            text = strong + text[len(weak):]
            break
    text = text[0].upper() + text[1:]
    if text[-1] not in ".!?":
        text += "."
    return text


def formalize_bullets(values: Iterable[Any], *, max_items: int = 10) -> list[str]:
    """Return clean, professional bullet content without inventing facts."""
    bullets: list[str] = []
    seen: set[str] = set()
    for value in values:
        sentence = _sentence(value)
        key = sentence.casefold()
        if sentence and key not in seen:
            bullets.append(sentence)
            seen.add(key)
        if len(bullets) >= max_items:
            break
    return bullets


def _experience_duties(item: dict[str, Any]) -> list[str]:
    values: list[Any] = []
    for key in ("duties", "responsibilities", "key_responsibilities"):
        values.extend(_items(item.get(key)))

    description = item.get("description")
    if not values and description:
        values.extend(_items(description))
    return formalize_bullets(values)


def _verified_achievements(item: dict[str, Any]) -> list[str]:
    values: list[Any] = []
    for key in ("achievements", "key_achievements", "verified_achievements"):
        values.extend(_items(item.get(key)))
    return formalize_bullets(values, max_items=6)


def formalize_resume_content(content: dict[str, Any]) -> dict[str, Any]:
    """
    Standardise CV wording and force responsibilities into point-form data.

    This function never creates employers, dates, metrics, qualifications or
    achievements. It only cleans and restructures supplied information.
    """
    result = deepcopy(content or {})
    experience = result.get("experience") or []
    formatted_experience: list[dict[str, Any]] = []

    for raw in experience:
        if not isinstance(raw, dict):
            continue
        item = deepcopy(raw)
        duties = _experience_duties(item)
        achievements = _verified_achievements(item)

        item["responsibilities"] = duties
        item["duties"] = duties
        item["achievements"] = achievements
        # Remove paragraph-style repetition after point-form conversion.
        if duties:
            item["description"] = ""
        formatted_experience.append(item)

    result["experience"] = formatted_experience

    summary = _text(result.get("professional_summary"))
    if summary:
        result["professional_summary"] = _sentence(summary)

    return result
