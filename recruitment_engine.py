from __future__ import annotations

from typing import Any


class AIRecruitmentEngine:
    """
    Recruitment matching engine.
    Replace heuristic scoring with embedding/vector search and LLM ranking
    in production.
    """

    def rank_candidates(
        self,
        job: dict[str, Any],
        candidates: list[dict[str, Any]],
    ) -> dict[str, Any]:
        ranked = []

        required = {s.lower() for s in job.get("skills", [])}

        for candidate in candidates:
            skills = {s.lower() for s in candidate.get("skills", [])}
            matched = sorted(required & skills)
            missing = sorted(required - skills)

            score = round((len(matched) / max(1, len(required))) * 100)

            ranked.append({
                "candidate_id": candidate.get("id"),
                "name": candidate.get("name"),
                "score": score,
                "matched_skills": matched,
                "missing_skills": missing,
                "recommended": score >= 70,
            })

        ranked.sort(key=lambda x: x["score"], reverse=True)

        return {
            "job_title": job.get("title"),
            "candidate_count": len(ranked),
            "rankings": ranked,
            "shortlist": [c for c in ranked if c["recommended"]],
        }
