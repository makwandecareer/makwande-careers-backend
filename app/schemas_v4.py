from datetime import date
from typing import Literal
from pydantic import BaseModel, EmailStr, Field

ApplicationStatus = Literal['submitted','reviewing','shortlisted','interview','rejected','withdrawn','hired']

class CertificationIn(BaseModel):
    name: str = Field(min_length=2, max_length=240)
    issuer: str | None = Field(default=None, max_length=240)
    issue_date: date | None = None
    expiry_date: date | None = None
    credential_id: str | None = Field(default=None, max_length=160)
    credential_url: str | None = None

class ProjectIn(BaseModel):
    name: str = Field(min_length=2, max_length=240)
    description: str | None = Field(default=None, max_length=6000)
    project_url: str | None = None
    technologies: list[str] = Field(default_factory=list, max_length=50)
    start_date: date | None = None
    end_date: date | None = None

class LanguageIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    proficiency: str | None = Field(default=None, max_length=80)

class ReferenceIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=200)
    relationship: str | None = Field(default=None, max_length=160)
    company: str | None = Field(default=None, max_length=240)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)

class EmployerProfileIn(BaseModel):
    company_name: str = Field(min_length=2, max_length=240)
    website_url: str | None = None
    industry: str | None = Field(default=None, max_length=160)
    location: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=5000)

class JobIn(BaseModel):
    title: str = Field(min_length=2, max_length=240)
    location: str | None = Field(default=None, max_length=200)
    employment_type: str | None = Field(default=None, max_length=80)
    workplace_type: str | None = Field(default=None, max_length=80)
    description: str = Field(min_length=20, max_length=20000)
    requirements: list[str] = Field(default_factory=list, max_length=100)
    skills: list[str] = Field(default_factory=list, max_length=100)
    closing_date: date | None = None
    is_active: bool = True

class ApplicationIn(BaseModel):
    job_id: str
    cv_id: str
    cover_note: str | None = Field(default=None, max_length=5000)

class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus

class ShortlistIn(BaseModel):
    candidate_user_id: str
    job_id: str | None = None
    notes: str | None = Field(default=None, max_length=3000)
