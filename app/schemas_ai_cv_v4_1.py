from typing import Any, Literal

from pydantic import BaseModel, Field


TemplateKey = Literal[
    "ats-standard",
    "graduate",
    "professional",
    "executive",
]


class GenerateCVRequest(BaseModel):
    target_role: str = Field(min_length=2, max_length=160)
    template_key: TemplateKey = "ats-standard"
    cv_id: str | None = None
    save_snapshot: bool = True


class ImproveSummaryRequest(BaseModel):
    target_role: str = Field(min_length=2, max_length=160)
    current_summary: str = Field(default="", max_length=5000)
    verified_strengths: list[str] = Field(default_factory=list, max_length=30)
    cv_id: str | None = None
    save_revision: bool = True


class ImproveExperienceRequest(BaseModel):
    job_title: str = Field(min_length=2, max_length=160)
    duties: list[str] = Field(min_length=1, max_length=30)
    verified_achievements: list[str] = Field(default_factory=list, max_length=30)
    target_role: str | None = Field(default=None, max_length=160)
    cv_id: str | None = None
    save_revision: bool = True


class ATSScoreRequest(BaseModel):
    cv_content: dict[str, Any]
    job_description: str = Field(min_length=20, max_length=20000)
    target_role: str | None = Field(default=None, max_length=160)
    cv_id: str | None = None
    save_history: bool = True


class ATSScoreResponse(BaseModel):
    score: int = Field(ge=0, le=100)
    matched_keywords: list[str]
    missing_keywords: list[str]
    recommendations: list[str]


class GeneratedCVResponse(BaseModel):
    title: str
    target_role: str
    template_key: TemplateKey
    content: dict[str, Any]
    warnings: list[str] = Field(default_factory=list)
    snapshot_id: str | None = None


class TextImprovementResponse(BaseModel):
    text: str
    warnings: list[str] = Field(default_factory=list)
    revision_id: str | None = None


class ExportCVRequest(BaseModel):
    filename: str = Field(default="makwande-careers-cv", min_length=1, max_length=120)
    template_key: TemplateKey = "ats-standard"
    cv_content: dict[str, Any]


class RevisionAcceptRequest(BaseModel):
    accepted: bool = True
