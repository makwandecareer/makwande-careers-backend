from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/analytics", tags=["Employer Analytics"])


@router.get("/employer/{company_id}")
def employer_analytics(company_id: int):
    """
    Placeholder employer analytics endpoint.
    Replace values with aggregated database metrics.
    """
    return {
        "company_id": company_id,
        "jobs": {
            "active": 12,
            "closed": 34,
            "draft": 3,
        },
        "applications": {
            "total": 842,
            "shortlisted": 97,
            "interviews": 31,
            "offers": 12,
            "hires": 9,
        },
        "recruitment_metrics": {
            "average_time_to_hire_days": 24,
            "application_to_interview_rate": 3.7,
            "offer_acceptance_rate": 75.0,
        },
        "candidate_insights": {
            "top_skills": [
                "Project Management",
                "Python",
                "Leadership",
                "Communication",
                "Data Analysis",
            ],
            "top_locations": [
                "Cape Town",
                "Johannesburg",
                "Durban",
            ],
        },
        "ai_insights": [
            "Increase salary transparency to improve application volume.",
            "Review job descriptions with low conversion rates.",
            "High-performing candidates frequently match Project Management skills.",
        ],
    }
