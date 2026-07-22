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


CandidateLevel = Literal[
    "graduate",
    "early-career",
    "mid-career",
    "senior",
    "executive",
]


class ImportedContact(BaseModel):
    full_name: str = Field(default="", max_length=200)
    email: str = Field(default="", max_length=320)
    phone: str = Field(default="", max_length=80)
    location: str = Field(default="", max_length=200)
    linkedin_url: str = Field(default="", max_length=500)
    portfolio_url: str = Field(default="", max_length=500)


class ImportedExperience(BaseModel):
    company: str = Field(default="", max_length=240)
    job_title: str = Field(default="", max_length=200)
    start_date: str = Field(default="", max_length=40)
    end_date: str = Field(default="", max_length=40)
    description: str = Field(default="", max_length=6000)
    achievements: list[str] = Field(default_factory=list, max_length=20)


class ImportedEducation(BaseModel):
    institution: str = Field(default="", max_length=240)
    qualification: str = Field(default="", max_length=240)
    field_of_study: str = Field(default="", max_length=240)
    start_date: str = Field(default="", max_length=40)
    end_date: str = Field(default="", max_length=40)
    description: str = Field(default="", max_length=3000)


class ImportedProject(BaseModel):
    name: str = Field(default="", max_length=240)
    description: str = Field(default="", max_length=4000)
    technologies: list[str] = Field(default_factory=list, max_length=30)


class ImportedCertification(BaseModel):
    name: str = Field(default="", max_length=240)
    issuer: str = Field(default="", max_length=240)
    date: str = Field(default="", max_length=40)


class CVImportDraft(BaseModel):
    candidate_level: CandidateLevel
    suggested_template: TemplateKey = "ats-standard"
    personal_details: ImportedContact
    professional_title: str = Field(default="", max_length=200)
    professional_summary: str = Field(default="", max_length=3000)
    skills: list[str] = Field(default_factory=list, max_length=60)
    experience: list[ImportedExperience] = Field(default_factory=list, max_length=30)
    education: list[ImportedEducation] = Field(default_factory=list, max_length=20)
    projects: list[ImportedProject] = Field(default_factory=list, max_length=20)
    certifications: list[ImportedCertification] = Field(default_factory=list, max_length=30)
    languages: list[str] = Field(default_factory=list, max_length=30)
    missing_details: list[str] = Field(default_factory=list, max_length=30)
    follow_up_questions: list[str] = Field(default_factory=list, max_length=20)
    facts_to_verify: list[str] = Field(default_factory=list, max_length=30)


class ImportCVRequest(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    target_role: str = Field(min_length=2, max_length=160)
    template_key: TemplateKey = "ats-standard"
    content: dict[str, Any]
