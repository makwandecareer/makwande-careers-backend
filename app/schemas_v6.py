from typing import Any

from pydantic import BaseModel, Field


class JobMatchRequest(BaseModel):
    cv_content: dict[str, Any]
    job_description: str = Field(min_length=20, max_length=20000)


class JobMatchResponse(BaseModel):
    score: int = Field(ge=0, le=100)
    strengths: list[str]
    missing_keywords: list[str]
    recommendations: list[str]


class CoverLetterRequest(BaseModel):
    candidate_name: str = Field(min_length=2, max_length=200)
    target_role: str = Field(min_length=2, max_length=160)
    company_name: str = Field(min_length=2, max_length=240)
    verified_strengths: list[str] = Field(default_factory=list, max_length=30)
    verified_experience: list[str] = Field(default_factory=list, max_length=30)


class InterviewPrepRequest(BaseModel):
    target_role: str = Field(min_length=2, max_length=160)
    job_description: str = Field(min_length=20, max_length=20000)
    candidate_strengths: list[str] = Field(default_factory=list, max_length=30)


class SkillsGapRequest(BaseModel):
    current_skills: list[str] = Field(default_factory=list, max_length=100)
    target_role: str = Field(min_length=2, max_length=160)
    job_description: str = Field(min_length=20, max_length=20000)


class CareerRoadmapRequest(BaseModel):
    current_role: str | None = Field(default=None, max_length=160)
    target_role: str = Field(min_length=2, max_length=160)
    qualifications: list[str] = Field(default_factory=list, max_length=50)
    skills: list[str] = Field(default_factory=list, max_length=100)
