from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from psycopg.types.json import Jsonb

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
    values["hiring_preferences"] = Jsonb(values["hiring_preferences"])
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


@router.get("/summary")
def employer_summary(user: dict = Depends(get_current_user)):
    company = company_for(str(user["id"]))
    if not company:
        return {"company": None, "metrics": {"total_jobs": 0, "open_jobs": 0, "draft_jobs": 0, "closed_jobs": 0}, "recent_jobs": []}
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)::int AS total_jobs,
                COUNT(*) FILTER (WHERE status='published')::int AS open_jobs,
                COUNT(*) FILTER (WHERE status='draft')::int AS draft_jobs,
                COUNT(*) FILTER (WHERE status='closed')::int AS closed_jobs
                FROM employer_jobs WHERE company_id=%s
                """,
                (company["id"],),
            )
            metrics = dict(cursor.fetchone())
            cursor.execute("SELECT * FROM employer_jobs WHERE company_id=%s ORDER BY created_at DESC LIMIT 5", (company["id"],))
            recent_jobs = [serialize(row) for row in cursor.fetchall()]
    return {"company": company, "metrics": metrics, "recent_jobs": recent_jobs}


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
    values["screening_questions"] = Jsonb(values["screening_questions"])
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


@router.get("/jobs/{job_id}")
def get_job(job_id: UUID, company: dict = Depends(require_company)):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM employer_jobs WHERE id=%s AND company_id=%s LIMIT 1", (str(job_id), company["id"]))
            row = cursor.fetchone()
    if not row:
        raise HTTPException(404, "Vacancy not found.")
    return {"job": serialize(row)}


@router.put("/jobs/{job_id}")
def update_job(job_id: UUID, payload: JobPayload, company: dict = Depends(require_company)):
    values = payload.model_dump(mode="json")
    values["screening_questions"] = Jsonb(values["screening_questions"])
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE employer_jobs SET
                title=%(title)s,department=%(department)s,location=%(location)s,workplace_type=%(workplace_type)s,
                employment_type=%(employment_type)s,seniority_level=%(seniority_level)s,salary_min=%(salary_min)s,
                salary_max=%(salary_max)s,salary_currency=%(salary_currency)s,salary_visible=%(salary_visible)s,
                summary=%(summary)s,responsibilities=%(responsibilities)s,requirements=%(requirements)s,
                skills=%(skills)s,benefits=%(benefits)s,screening_questions=%(screening_questions)s,
                closing_date=%(closing_date)s,updated_at=CURRENT_TIMESTAMP
                WHERE id=%(job_id)s AND company_id=%(company_id)s RETURNING *
                """,
                {**values, "job_id": str(job_id), "company_id": company["id"]},
            )
            row = cursor.fetchone()
        connection.commit()
    if not row:
        raise HTTPException(404, "Vacancy not found.")
    return {"job": serialize(row)}


@router.delete("/jobs/{job_id}", status_code=204)
def delete_job(job_id: UUID, company: dict = Depends(require_company)):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM employer_jobs WHERE id=%s AND company_id=%s RETURNING id", (str(job_id), company["id"]))
            row = cursor.fetchone()
        connection.commit()
    if not row:
        raise HTTPException(404, "Vacancy not found.")


def set_status(job_id: UUID, new_status: Literal["published", "closed"], company: dict):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("UPDATE employer_jobs SET status=%s,updated_at=CURRENT_TIMESTAMP WHERE id=%s AND company_id=%s RETURNING *", (new_status, str(job_id), company["id"]))
            row = cursor.fetchone()
        connection.commit()
    if not row:
        raise HTTPException(404, "Vacancy not found.")
    return {"job": serialize(row)}


@router.post("/jobs/{job_id}/publish")
def publish_job(job_id: UUID, company: dict = Depends(require_company)):
    return set_status(job_id, "published", company)


@router.post("/jobs/{job_id}/close")
def close_job(job_id: UUID, company: dict = Depends(require_company)):
    return set_status(job_id, "closed", company)


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
