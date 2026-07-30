from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, EmailStr, Field
from fastapi import APIRouter

router = APIRouter(prefix="/employers", tags=["Employer Portal"])


class CompanySize(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"


class CompanyRegistration(BaseModel):
    company_name: str = Field(..., min_length=2)
    registration_number: str | None = None
    industry: str
    company_size: CompanySize
    website: str | None = None
    contact_email: EmailStr


class RecruiterInvitation(BaseModel):
    full_name: str
    email: EmailStr
    role: str = "Recruiter"


@router.post("/companies")
def register_company(payload: CompanyRegistration):
    return {
        "company": payload.model_dump(),
        "status": "registered",
        "next_steps": [
            "Verify company",
            "Invite recruiters",
            "Create your first job posting",
        ],
    }


@router.post("/recruiters/invite")
def invite_recruiter(payload: RecruiterInvitation):
    return {
        "status": "invited",
        "recruiter": payload.model_dump(),
    }


@router.get("/dashboard")
def employer_dashboard():
    return {
        "jobs": 0,
        "active_recruiters": 0,
        "candidates": 0,
        "interviews": 0,
        "hires": 0,
    }
