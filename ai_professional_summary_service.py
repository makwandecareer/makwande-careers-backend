from __future__ import annotations

from typing import Any


class AIProfessionalSummaryService:
    """
    Generates professional summaries.
    This service is AI-ready. Replace the placeholder implementation
    with your preferred LLM provider when integrating AI.
    """

    def generate(
        self,
        profile: dict[str, Any],
        experience: list[dict[str, Any]],
        target_role: str | None = None,
        seniority: str = "professional",
    ) -> dict[str, Any]:

        years = self._estimate_years(experience)
        role = target_role or profile.get("headline") or "Professional"

        summary = (
            f"{role} with approximately {years} years of experience, "
            f"demonstrating strong technical expertise, leadership, "
            f"problem-solving abilities, and a commitment to delivering "
            f"high-quality results in fast-paced environments."
        )

        return {
            "summary": summary,
            "variants": {
                "graduate": self._graduate(role),
                "professional": summary,
                "executive": self._executive(role, years),
            },
            "keywords": self._keywords(profile, experience),
            "ai_ready": True,
        }

    def _estimate_years(self, experience: list[dict[str, Any]]) -> int:
        return max(1, len(experience) * 2)

    def _keywords(
        self,
        profile: dict[str, Any],
        experience: list[dict[str, Any]],
    ) -> list[str]:
        keywords = set()

        headline = profile.get("headline")
        if headline:
            keywords.add(headline)

        for item in experience:
            for key in ("position", "industry", "skills"):
                value = item.get(key)
                if isinstance(value, str):
                    keywords.add(value)

        return sorted(keywords)

    def _graduate(self, role: str) -> str:
        return (
            f"Motivated {role} eager to contribute strong analytical, "
            "communication, and problem-solving skills while building "
            "a successful professional career."
        )

    def _executive(self, role: str, years: int) -> str:
        return (
            f"Strategic {role} with approximately {years} years of "
            "leadership experience driving operational excellence, "
            "business growth, stakeholder engagement, and organisational success."
        )
