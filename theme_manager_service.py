from __future__ import annotations

from copy import deepcopy
from typing import Any


DEFAULT_THEME = "modern"

THEMES = {
    "modern": {
        "version": "2.0",
        "font": "Inter",
        "primary_color": "#0F766E",
        "secondary_color": "#E6FFFA",
        "layout": "modern",
    },
    "professional": {
        "version": "2.0",
        "font": "Calibri",
        "primary_color": "#1F2937",
        "secondary_color": "#F3F4F6",
        "layout": "professional",
    },
    "executive": {
        "version": "2.0",
        "font": "Georgia",
        "primary_color": "#111827",
        "secondary_color": "#F9FAFB",
        "layout": "executive",
    },
}


class ThemeManagerService:
    """
    Handles template versions, themes and design settings.
    """

    def list_themes(self) -> list[str]:
        return sorted(THEMES.keys())

    def get_theme(self, theme: str) -> dict[str, Any]:
        if theme not in THEMES:
            theme = DEFAULT_THEME
        return deepcopy(THEMES[theme])

    def apply_theme(self, draft) -> dict[str, Any]:
        selected = getattr(draft, "template_id", DEFAULT_THEME)
        theme = self.get_theme(selected)

        design = deepcopy(getattr(draft, "design", {}) or {})
        design.update(theme)

        return design

    def current_version(self, draft) -> str:
        selected = getattr(draft, "template_id", DEFAULT_THEME)
        return self.get_theme(selected)["version"]

    def upgrade(self, draft) -> dict[str, Any]:
        design = self.apply_theme(draft)
        return {
            "template_id": getattr(draft, "template_id", DEFAULT_THEME),
            "template_version": design["version"],
            "design": design,
        }
