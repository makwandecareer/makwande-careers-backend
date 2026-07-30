from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/v1", tags=["Public API"])


@router.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "Makwande Careers Public API",
        "version": "1.0.0",
    }


@router.post("/cv/analyze")
def analyze_cv():
    return {
        "endpoint": "cv/analyze",
        "status": "available",
        "description": "Analyze a CV and return ATS insights."
    }


@router.post("/job/match")
def job_match():
    return {
        "endpoint": "job/match",
        "status": "available",
        "description": "Match a candidate profile against a job."
    }


@router.post("/cover-letter/generate")
def cover_letter():
    return {
        "endpoint": "cover-letter/generate",
        "status": "available",
        "description": "Generate a tailored cover letter."
    }


@router.post("/interview/prepare")
def interview_prepare():
    return {
        "endpoint": "interview/prepare",
        "status": "available",
        "description": "Generate interview questions and preparation guidance."
    }


@router.get("/subscription/features")
def subscription_features():
    return {
        "trial_14_day": [
            "Unlimited CV Builder",
            "ATS Score",
            "Basic Templates",
        ],
        "premium_30_day": [
            "Unlimited CV Builder",
            "Premium Templates",
            "AI Career Tools",
            "Cover Letter Generator",
            "Interview Preparation",
        ],
        "enterprise": [
            "Employer Portal",
            "Recruitment APIs",
            "Advanced Analytics",
            "Priority Support",
        ],
    }
