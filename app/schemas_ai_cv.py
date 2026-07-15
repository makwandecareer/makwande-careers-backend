from typing import Any
from pydantic import BaseModel, Field

class GenerateCVRequest(BaseModel):
    target_role: str = Field(min_length=2, max_length=160)
    template_key: str = Field(default="ats-standard", max_length=80)

class ImproveSummaryRequest(BaseModel):
    target_role: str = Field(min_length=2, max_length=160)
    current_summary: str = Field(default="", max_length=5000)
    verified_strengths: list[str] = Field(default_factory=list, max_length=30)

class ImproveExperienceRequest(BaseModel):
    job_title: str = Field(min_length=2, max_length=160)
    duties: list[str] = Field(min_length=1, max_length=30)
    verified_achievements: list[str] = Field(default_factory=list, max_length=30)

class ATSScoreRequest(BaseModel):
    cv_content: dict[str, Any]
    job_description: str = Field(min_length=20, max_length=20000)

class ATSScoreResponse(BaseModel):
    score: int = Field(ge=0, le=100)
    matched_keywords: list[str]
    missing_keywords: list[str]
    recommendations: list[str]

class GeneratedCVResponse(BaseModel):
    title: str
    target_role: str
    template_key: str
    content: dict[str, Any]
    warnings: list[str] = Field(default_factory=list)

class TextImprovementResponse(BaseModel):
    text: str
    warnings: list[str] = Field(default_factory=list)

class ExportCVRequest(BaseModel):
    filename: str = Field(default="makwande-careers-cv", min_length=1, max_length=120)
    cv_content: dict[str, Any]
