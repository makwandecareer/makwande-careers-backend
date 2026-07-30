from __future__ import annotations

from typing import Any


class AICareerCoachService:
    """
    AI-ready career coaching service.
    Replace heuristic logic with an LLM and labor-market data provider
    for personalized recommendations.
    """

    def advise(
        self,
        profile: dict[str, Any],
        experience: list[dict[str, Any]],
        skills: list[str],
        target_role: str | None = None,
    ) -> dict[str, Any]:

        years = max(1, len(experience) * 2)
        role = target_role or profile.get("headline", "Professional")

        return {
            "career_level": self._career_level(years),
            "target_role": role,
            "recommended_skills": self._recommended_skills(skills),
            "recommended_certifications": self._certifications(role),
            "career_actions": [
                "Tailor your CV for each application.",
                "Build a portfolio of measurable achievements.",
                "Maintain an optimized LinkedIn profile.",
                "Network consistently within your industry.",
                "Apply for roles that match at least 70% of your skills."
            ],
            "next_roles": self._next_roles(role),
            "learning_plan": {
                "30_days": "Strengthen technical and communication skills.",
                "90_days": "Complete one industry-recognized certification.",
                "180_days": "Lead or contribute to a high-impact project."
            },
            "ai_ready": True,
        }

    def _career_level(self, years: int) -> str:
        if years < 2:
            return "Graduate / Entry Level"
        if years < 5:
            return "Mid-Level Professional"
        if years < 10:
            return "Senior Professional"
        return "Executive / Leadership"

    def _recommended_skills(self, skills: list[str]) -> list[str]:
        baseline = {
            "Leadership",
            "Communication",
            "Project Management",
            "Data Analysis",
            "Problem Solving",
            "Digital Literacy",
        }
        return sorted(baseline - set(skills))

    def _certifications(self, role: str) -> list[str]:
        return [
            f"Industry certification relevant to {role}",
            "Project Management (PMP/PRINCE2 or equivalent)",
            "Advanced Microsoft Excel",
            "Health & Safety certification (where applicable)",
        ]

    def _next_roles(self, role: str) -> list[str]:
        return [
            role,
            f"Senior {role}",
            f"Lead {role}",
            f"{role} Manager",
        ]
