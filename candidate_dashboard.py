from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/dashboard", tags=["Candidate Dashboard"])


@router.get("/{candidate_id}")
def candidate_dashboard(candidate_id: int):
    """
    Placeholder dashboard endpoint.
    Replace static values with database queries and analytics services.
    """
    return {
        "candidate_id": candidate_id,
        "profile_completion": 92,
        "ats_score": 86,
        "job_matches": 18,
        "applications": {
            "submitted": 24,
            "shortlisted": 6,
            "interviews": 3,
            "offers": 1,
        },
        "cv": {
            "last_updated": "2026-07-30",
            "downloads": 41,
        },
        "ai": {
            "recommendations": [
                "Add measurable achievements to recent role.",
                "Complete your LinkedIn profile.",
                "Tailor your CV to target job descriptions."
            ],
            "interview_readiness": 81,
        },
        "subscription": {
            "plan": "premium",
            "status": "active",
        },
    }
