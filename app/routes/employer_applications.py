from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from psycopg.types.json import Jsonb

from app.database import get_connection
from app.dependencies import get_current_user
from app.routes.employer import require_company, serialize


router = APIRouter(
    prefix="/employer",
    tags=["Employer Applications"],
)


ApplicationStatus = Literal[
    "submitted",
    "reviewing",
    "shortlisted",
    "interview",
    "offered",
    "hired",
    "rejected",
    "withdrawn",
]


class ApplicationStatusPayload(BaseModel):
    status: ApplicationStatus


class ApplicationNotePayload(BaseModel):
    note: str = Field(min_length=1, max_length=5000)
    is_private: bool = True


def get_owned_application(
    application_id: UUID,
    company: dict,
) -> dict:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    application.*,
                    job.title AS job_title,
                    job.department,
                    job.location AS job_location,
                    job.workplace_type,
                    job.employment_type,
                    job.seniority_level,
                    job.status AS job_status,
                    candidate.email AS candidate_email,
                    candidate.email AS candidate_name,
                    profile.phone AS candidate_phone,
                    profile.location AS candidate_location,
                    profile.professional_title,
                    cv.title AS cv_title,
                    cv.template_key AS cv_template_key
                FROM employer_job_applications application
                JOIN employer_jobs job
                    ON job.id = application.job_id
                JOIN users candidate
                    ON candidate.id = application.candidate_user_id
                LEFT JOIN profiles profile
                    ON profile.user_id = application.candidate_user_id
                LEFT JOIN cvs cv
                    ON cv.id = application.cv_id
                WHERE application.id = %s
                  AND application.company_id = %s
                LIMIT 1
                """,
                (
                    str(application_id),
                    company["id"],
                ),
            )

            row = cursor.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found.",
        )

    return serialize(row)


@router.get("/applications")
def list_applications(
    status_filter: ApplicationStatus | None = Query(
        default=None,
        alias="status",
    ),
    job_id: UUID | None = None,
    search: str | None = Query(
        default=None,
        max_length=160,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    company: dict = Depends(require_company),
):
    conditions = [
        "application.company_id = %(company_id)s",
    ]

    values: dict = {
        "company_id": company["id"],
        "limit": limit,
        "offset": offset,
    }

    if status_filter:
        conditions.append(
            "application.status = %(application_status)s"
        )
        values["application_status"] = status_filter

    if job_id:
        conditions.append(
            "application.job_id = %(job_id)s"
        )
        values["job_id"] = str(job_id)

    if search and search.strip():
        conditions.append(
            """
            (
                candidate.email ILIKE %(search)s
                OR profile.professional_title ILIKE %(search)s
                OR job.title ILIKE %(search)s
                OR job.department ILIKE %(search)s
            )
            """
        )
        values["search"] = f"%{search.strip()}%"

    where_clause = " AND ".join(conditions)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT COUNT(*)::int AS total
                FROM employer_job_applications application
                JOIN employer_jobs job
                    ON job.id = application.job_id
                JOIN users candidate
                    ON candidate.id = application.candidate_user_id
                LEFT JOIN profiles profile
                    ON profile.user_id = application.candidate_user_id
                WHERE {where_clause}
                """,
                values,
            )

            total = cursor.fetchone()["total"]

            cursor.execute(
                f"""
                SELECT
                    application.*,
                    job.title AS job_title,
                    job.department,
                    job.location AS job_location,
                    job.workplace_type,
                    job.employment_type,
                    candidate.email AS candidate_email,
                    candidate.email AS candidate_name,
                    profile.phone AS candidate_phone,
                    profile.location AS candidate_location,
                    profile.professional_title,
                    cv.title AS cv_title,
                    cv.template_key AS cv_template_key
                FROM employer_job_applications application
                JOIN employer_jobs job
                    ON job.id = application.job_id
                JOIN users candidate
                    ON candidate.id = application.candidate_user_id
                LEFT JOIN profiles profile
                    ON profile.user_id = application.candidate_user_id
                LEFT JOIN cvs cv
                    ON cv.id = application.cv_id
                WHERE {where_clause}
                ORDER BY
                    application.updated_at DESC,
                    application.created_at DESC
                LIMIT %(limit)s
                OFFSET %(offset)s
                """,
                values,
            )

            applications = [
                serialize(row)
                for row in cursor.fetchall()
            ]

    return {
        "applications": applications,
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(applications) < total,
        },
    }


@router.get("/jobs/{job_id}/applications")
def list_job_applications(
    job_id: UUID,
    company: dict = Depends(require_company),
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    title,
                    department,
                    location,
                    status
                FROM employer_jobs
                WHERE id = %s
                  AND company_id = %s
                LIMIT 1
                """,
                (
                    str(job_id),
                    company["id"],
                ),
            )

            job = cursor.fetchone()

            if not job:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Vacancy not found.",
                )

            cursor.execute(
                """
                SELECT
                    application.*,
                    candidate.email AS candidate_email,
                    candidate.email AS candidate_name,
                    profile.phone AS candidate_phone,
                    profile.location AS candidate_location,
                    profile.professional_title,
                    cv.title AS cv_title,
                    cv.template_key AS cv_template_key
                FROM employer_job_applications application
                JOIN users candidate
                    ON candidate.id = application.candidate_user_id
                LEFT JOIN profiles profile
                    ON profile.user_id = application.candidate_user_id
                LEFT JOIN cvs cv
                    ON cv.id = application.cv_id
                WHERE application.job_id = %s
                  AND application.company_id = %s
                ORDER BY
                    application.updated_at DESC,
                    application.created_at DESC
                """,
                (
                    str(job_id),
                    company["id"],
                ),
            )

            applications = [
                serialize(row)
                for row in cursor.fetchall()
            ]

    return {
        "job": serialize(job),
        "applications": applications,
        "total": len(applications),
    }


@router.get("/applications/{application_id}")
def application_detail(
    application_id: UUID,
    company: dict = Depends(require_company),
):
    application = get_owned_application(
        application_id,
        company,
    )

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    note.id,
                    note.note,
                    note.is_private,
                    note.created_at,
                    note.updated_at,
                    author.email AS author_email
                FROM employer_application_notes note
                JOIN users author
                    ON author.id = note.author_user_id
                WHERE note.application_id = %s
                ORDER BY note.created_at DESC
                """,
                (str(application_id),),
            )

            notes = [
                serialize(row)
                for row in cursor.fetchall()
            ]

            cursor.execute(
                """
                SELECT *
                FROM employer_application_interviews
                WHERE application_id = %s
                ORDER BY scheduled_at DESC
                """,
                (str(application_id),),
            )

            interviews = [
                serialize(row)
                for row in cursor.fetchall()
            ]

            cursor.execute(
                """
                SELECT *
                FROM employer_application_activity
                WHERE application_id = %s
                ORDER BY created_at DESC
                """,
                (str(application_id),),
            )

            activity = [
                serialize(row)
                for row in cursor.fetchall()
            ]

    return {
        "application": application,
        "notes": notes,
        "interviews": interviews,
        "activity": activity,
    }


@router.put("/applications/{application_id}/status")
def update_application_status(
    application_id: UUID,
    payload: ApplicationStatusPayload,
    user: dict = Depends(get_current_user),
    company: dict = Depends(require_company),
):
    current = get_owned_application(
        application_id,
        company,
    )

    if current["status"] == payload.status:
        return {
            "application": current,
            "changed": False,
        }

    if current["status"] == "withdrawn":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A withdrawn application cannot be updated.",
        )

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE employer_job_applications
                SET
                    status = %s,
                    last_activity_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                  AND company_id = %s
                RETURNING *
                """,
                (
                    payload.status,
                    str(application_id),
                    company["id"],
                ),
            )

            updated = cursor.fetchone()

            if not updated:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Application not found.",
                )

            cursor.execute(
                """
                INSERT INTO employer_application_activity
                (
                    application_id,
                    actor_user_id,
                    activity_type,
                    from_status,
                    to_status,
                    metadata
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    str(application_id),
                    str(user["id"]),
                    "status_changed",
                    current["status"],
                    payload.status,
                    Jsonb({}),
                ),
            )

        connection.commit()

    return {
        "application": serialize(updated),
        "changed": True,
    }


@router.post(
    "/applications/{application_id}/notes",
    status_code=status.HTTP_201_CREATED,
)
def add_application_note(
    application_id: UUID,
    payload: ApplicationNotePayload,
    user: dict = Depends(get_current_user),
    company: dict = Depends(require_company),
):
    get_owned_application(
        application_id,
        company,
    )

    note_text = payload.note.strip()

    if not note_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Note cannot be empty.",
        )

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO employer_application_notes
                (
                    application_id,
                    author_user_id,
                    note,
                    is_private
                )
                VALUES (%s, %s, %s, %s)
                RETURNING *
                """,
                (
                    str(application_id),
                    str(user["id"]),
                    note_text,
                    payload.is_private,
                ),
            )

            note = cursor.fetchone()

            cursor.execute(
                """
                INSERT INTO employer_application_activity
                (
                    application_id,
                    actor_user_id,
                    activity_type,
                    metadata
                )
                VALUES (%s, %s, %s, %s)
                """,
                (
                    str(application_id),
                    str(user["id"]),
                    "note_added",
                    Jsonb(
                        {
                            "note_id": str(note["id"]),
                            "is_private": payload.is_private,
                        }
                    ),
                ),
            )

            cursor.execute(
                """
                UPDATE employer_job_applications
                SET
                    last_activity_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                  AND company_id = %s
                """,
                (
                    str(application_id),
                    company["id"],
                ),
            )

        connection.commit()

    return {
        "note": serialize(note),
    }