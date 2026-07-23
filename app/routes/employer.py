from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.database import get_connection
from app.dependencies import get_current_user

router = APIRouter(prefix="/employer", tags=["Employer Platform"])


class CompanyPayload(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    registration_number: str | None = None
    industry: str | None = None
    company_size: str | None = None
    website: str | None = None
    phone: str | None = None
    email: str | None = None
    location: str | None = None
    description: str | None = None
    hiring_preferences: dict[str, Any] = Field(default_factory=dict)


class JobPayload(BaseModel):
    title: str = Field(min_length=2, max_length=180)
    department: str | None = None
    location: str | None = None
    workplace_type: Literal["onsite", "hybrid", "remote"] = "onsite"
    employment_type: Literal["full_time", "part_time", "contract", "temporary", "internship", "learnership"] = "full_time"
    seniority_level: str | None = None
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    salary_currency: str = "ZAR"
    salary_visible: bool = False
    summary: str | None = None
    responsibilities: list[str] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    benefits: list[str] = Field(default_factory=list)
    screening_questions: list[dict[str, Any]] = Field(default_factory=list)
    closing_date: date | None = None


def serialize(row):
    data = dict(row)
    for key, value in list(data.items()):
        if hasattr(value, "isoformat"):
            data[key] = value.isoformat()
        elif isinstance(value, Decimal):
            data[key] = float(value)
    return data


def company_for(user_id: str):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM employer_companies WHERE owner_user_id=%s LIMIT 1", (user_id,))
            row = cursor.fetchone()
    return serialize(row) if row else None


def require_company(user: dict = Depends(get_current_user)):
    company = company_for(str(user["id"]))
    if not company:
        raise HTTPException(status_code=409, detail="Complete company registration before managing vacancies.")
    return company


@router.get("/company")
def get_company(user: dict = Depends(get_current_user)):
    return {"company": company_for(str(user["id"]))}


@router.put("/company")
def save_company(payload: CompanyPayload, user: dict = Depends(get_current_user)):
    values = payload.model_dump(mode="json")
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO employer_companies
                (owner_user_id,name,registration_number,industry,company_size,website,phone,email,location,description,hiring_preferences)
                VALUES (%(owner_user_id)s,%(name)s,%(registration_number)s,%(industry)s,%(company_size)s,%(website)s,%(phone)s,%(email)s,%(location)s,%(description)s,%(hiring_preferences)s)
                ON CONFLICT(owner_user_id) DO UPDATE SET
                name=EXCLUDED.name,registration_number=EXCLUDED.registration_number,industry=EXCLUDED.industry,
                company_size=EXCLUDED.company_size,website=EXCLUDED.website,phone=EXCLUDED.phone,email=EXCLUDED.email,
                location=EXCLUDED.location,description=EXCLUDED.description,hiring_preferences=EXCLUDED.hiring_preferences,
                updated_at=CURRENT_TIMESTAMP RETURNING *
                """,
                {**values, "owner_user_id": str(user["id"])},
            )
            row = cursor.fetchone()
        connection.commit()
    return {"company": serialize(row)}


@router.get("/jobs")
def list_jobs(company: dict = Depends(require_company)):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM employer_jobs WHERE company_id=%s ORDER BY created_at DESC", (company["id"],))
            rows = cursor.fetchall()
    return {"jobs": [serialize(row) for row in rows]}


@router.post("/jobs", status_code=status.HTTP_201_CREATED)
def create_job(payload: JobPayload, user: dict = Depends(get_current_user), company: dict = Depends(require_company)):
    values = payload.model_dump(mode="json")
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO employer_jobs
                (company_id,created_by,title,department,location,workplace_type,employment_type,seniority_level,
                 salary_min,salary_max,salary_currency,salary_visible,summary,responsibilities,requirements,skills,
                 benefits,screening_questions,closing_date)
                VALUES (%(company_id)s,%(created_by)s,%(title)s,%(department)s,%(location)s,%(workplace_type)s,
                 %(employment_type)s,%(seniority_level)s,%(salary_min)s,%(salary_max)s,%(salary_currency)s,
                 %(salary_visible)s,%(summary)s,%(responsibilities)s,%(requirements)s,%(skills)s,%(benefits)s,
                 %(screening_questions)s,%(closing_date)s) RETURNING *
                """,
                {**values, "company_id": company["id"], "created_by": str(user["id"])},
            )
            row = cursor.fetchone()
        connection.commit()
    return {"job": serialize(row)}


@router.post("/jobs/{job_id}/{action}")
def job_action(job_id: UUID, action: Literal["publish", "close"], company: dict = Depends(require_company)):
    new_status = "published" if action == "publish" else "closed"
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("UPDATE employer_jobs SET status=%s,updated_at=CURRENT_TIMESTAMP WHERE id=%s AND company_id=%s RETURNING *", (new_status, str(job_id), company["id"]))
            row = cursor.fetchone()
        connection.commit()
    if not row:
        raise HTTPException(404, "Vacancy not found.")
    return {"job": serialize(row)}


@router.post("/jobs/{job_id}/duplicate", status_code=201)
def duplicate_job(job_id: UUID, user: dict = Depends(get_current_user), company: dict = Depends(require_company)):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO employer_jobs
                (company_id,created_by,title,department,location,workplace_type,employment_type,seniority_level,
                 salary_min,salary_max,salary_currency,salary_visible,summary,responsibilities,requirements,skills,
                 benefits,screening_questions,closing_date,status)
                SELECT company_id,%s,title || ' (Copy)',department,location,workplace_type,employment_type,seniority_level,
                 salary_min,salary_max,salary_currency,salary_visible,summary,responsibilities,requirements,skills,
                 benefits,screening_questions,closing_date,'draft'
                FROM employer_jobs WHERE id=%s AND company_id=%s RETURNING *
                """,
                (str(user["id"]), str(job_id), company["id"]),
            )
            row = cursor.fetchone()
        connection.commit()
    if not row:
        raise HTTPException(404, "Vacancy not found.")
    return {"job": serialize(row)}
