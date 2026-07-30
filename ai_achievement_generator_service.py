from __future__ import annotations

from typing import Any


class AIAchievementGeneratorService:
    """
    Converts responsibilities into measurable, ATS-friendly achievements.
    Replace the placeholder generation logic with an LLM implementation
    when AI integration is enabled.
    """

    ACTION_VERBS = [
        "Led", "Improved", "Implemented", "Optimized", "Reduced",
        "Delivered", "Managed", "Coordinated", "Developed", "Increased"
    ]

    def generate(
        self,
        responsibilities: list[str],
        metrics: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        metrics = metrics or {}
        achievements = []

        for i, duty in enumerate(responsibilities):
            verb = self.ACTION_VERBS[i % len(self.ACTION_VERBS)]
            kpi = metrics.get(i) or metrics.get(str(i))
            sentence = self._build_sentence(verb, duty, kpi)
            achievements.append(sentence)

        return {
            "achievements": achievements,
            "recommendations": [
                "Quantify results wherever possible.",
                "Include percentages, costs, time saved, or production volumes.",
                "Start every achievement with a strong action verb.",
                "Align achievements with the target job description."
            ],
            "ai_ready": True,
        }

    def _build_sentence(self, verb: str, duty: str, kpi: Any) -> str:
        duty = duty.strip().rstrip(".")
        if kpi:
            return f"{verb} {duty}, achieving {kpi}."
        return (
            f"{verb} {duty}, contributing to improved operational "
            "efficiency and business performance."
        )
