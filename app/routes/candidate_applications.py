from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from psycopg.errors import UniqueViolation
from psycopg.types.json import Jsonb

from app.database import get_connection
from app.dependencies import get_current_user
from app.routes.employer import serialize


router = APIRouter(
    tags=["Candidate Applications"],
)


class CandidateApplicationPayload(BaseModel):
    cv_id: UUID
    cover_note: str | None = Field(
        default=None,
        max_length=5000,
    )


def get_candidate_application(
    application_id: UUID,
    candidate_user_id: str,
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
                    job.summary AS job_summary,
                    job.closing_date,
                    company.name AS company_name,
                    company.industry AS company_industry,
                    company.location AS company_location,
                    company.website AS company_website,
                    cv.title AS cv_title,
                    cv.template_key AS cv_template_key
                FROM employer_job_applications application
                JOIN employer_jobs job
                    ON job.id = application.job_id
                JOIN employer_companies company
                    ON company.id = application.company_id
                LEFT JOIN cvs cv
                    ON cv.id = application.cv_id
                WHERE application.id = %s
                  AND application.candidate_user_id = %s
                LIMIT 1
                """,
                (
                    str(application_id),
                    candidate_user_id,
                ),
            )

            row = cursor.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found.",
        )

    return serialize(row)


@router.get("/jobs")
def browse_published_jobs(
    search: str | None = Query(
        default=None,
        max_length=160,
    ),
    location: str | None = Query(
        default=None,
        max_length=160,
    ),
    employment_type: str | None = Query(
        default=None,
        max_length=40,
    ),
    workplace_type: str | None = Query(
        default=None,
        max_length=30,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
):
    conditions = [
        "job.status = 'published'",
        """
        (
            job.closing_date IS NULL
            OR job.closing_date >= CURRENT_DATE
        )
        """,
    ]

    values: dict = {
        "limit": limit,
        "offset": offset,
    }

    if search:
        conditions.append(
            """
            (
                job.title ILIKE %(search)s
                OR job.department ILIKE %(search)s
                OR job.summary ILIKE %(search)s
                OR company.name ILIKE %(search)s
                OR company.industry ILIKE %(search)s
            )
            """
        )
        values["search"] = f"%{search.strip()}%"

    if location:
        conditions.append(
            "job.location ILIKE %(location)s"
        )
        values["location"] = f"%{location.strip()}%"

    if employment_type:
        conditions.append(
            "job.employment_type = %(employment_type)s"
        )
        values["employment_type"] = employment_type

    if workplace_type:
        conditions.append(
            "job.workplace_type = %(workplace_type)s"
        )
        values["workplace_type"] = workplace_type

    where_clause = " AND ".join(conditions)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT COUNT(*)::int AS total
                FROM employer_jobs job
                JOIN employer_companies company
                    ON company.id = job.company_id
                WHERE {where_clause}
                """,
                values,
            )

            total = cursor.fetchone()["total"]

            cursor.execute(
                f"""
                SELECT
                    job.*,
                    company.name AS company_name,
                    company.industry AS company_industry,
                    company.location AS company_location,
                    company.verification_status
                FROM employer_jobs job
                JOIN employer_companies company
                    ON company.id = job.company_id
                WHERE {where_clause}
                ORDER BY job.created_at DESC
                LIMIT %(limit)s
                OFFSET %(offset)s
                """,
                values,
            )

            jobs = [
                serialize(row)
                for row in cursor.fetchall()
            ]

    return {
        "jobs": jobs,
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(jobs) < total,
        },
    }


@router.get("/jobs/{job_id}")
def published_job_detail(job_id: UUID):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    job.*,
                    company.name AS company_name,
                    company.industry AS company_industry,
                    company.company_size,
                    company.website AS company_website,
                    company.location AS company_location,
                    company.description AS company_description,
                    company.verification_status
                FROM employer_jobs job
                JOIN employer_companies company
                    ON company.id = job.company_id
                WHERE job.id = %s
                  AND job.status = 'published'
                  AND (
                      job.closing_date IS NULL
                      OR job.closing_date >= CURRENT_DATE
                  )
                LIMIT 1
                """,
                (str(job_id),),
            )

            job = cursor.fetchone()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found or no longer available.",
        )

    return {
        "job": serialize(job),
    }


@router.post(
    "/jobs/{job_id}/apply",
    status_code=status.HTTP_201_CREATED,
)
def apply_for_job(
    job_id: UUID,
    payload: CandidateApplicationPayload,
    user: dict = Depends(get_current_user),
):
    candidate_user_id = str(user["id"])

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    job.id,
                    job.company_id,
                    job.title,
                    job.status,
                    job.closing_date
                FROM employer_jobs job
                WHERE job.id = %s
                  AND job.status = 'published'
                  AND (
                      job.closing_date IS NULL
                      OR job.closing_date >= CURRENT_DATE
                  )
                LIMIT 1
                """,
                (str(job_id),),
            )

            job = cursor.fetchone()

            if not job:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Vacancy not found or applications are closed.",
                )

            cursor.execute(
                """
                SELECT id, title, template_key
                FROM cvs
                WHERE id = %s
                  AND owner_id = %s
                LIMIT 1
                """,
                (
                    str(payload.cv_id),
                    candidate_user_id,
                ),
            )

            cv = cursor.fetchone()

            if not cv:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="CV not found or does not belong to you.",
                )

            try:
                cursor.execute(
                    """
                    INSERT INTO employer_job_applications
                    (
                        job_id,
                        company_id,
                        candidate_user_id,
                        cv_id,
                        cover_note
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        str(job_id),
                        job["company_id"],
                        candidate_user_id,
                        str(payload.cv_id),
                        (
                            payload.cover_note.strip()
                            if payload.cover_note
                            else None
                        ),
                    ),
                )

                application = cursor.fetchone()

                cursor.execute(
                    """
                    INSERT INTO employer_application_activity
                    (
                        application_id,
                        actor_user_id,
                        activity_type,
                        to_status,
                        metadata
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        application["id"],
                        candidate_user_id,
                        "application_submitted",
                        "submitted",
                        Jsonb(
                            {
                                "job_id": str(job_id),
                                "cv_id": str(payload.cv_id),
                            }
                        ),
                    ),
                )

                connection.commit()

            except UniqueViolation as exc:
                connection.rollback()

                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="You have already applied for this vacancy.",
                ) from exc

    return {
        "message": "Application submitted successfully.",
        "application": serialize(application),
        "job": serialize(job),
        "cv": serialize(cv),
    }


@router.get("/my/applications")
def my_applications(
    application_status: str | None = Query(
        default=None,
        alias="status",
        max_length=30,
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
    user: dict = Depends(get_current_user),
):
    conditions = [
        "application.candidate_user_id = %(candidate_user_id)s",
    ]

    values: dict = {
        "candidate_user_id": str(user["id"]),
        "limit": limit,
        "offset": offset,
    }

    if application_status:
        conditions.append(
            "application.status = %(status)s"
        )
        values["status"] = application_status

    where_clause = " AND ".join(conditions)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT COUNT(*)::int AS total
                FROM employer_job_applications application
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
                    job.closing_date,
                    company.name AS company_name,
                    company.industry AS company_industry,
                    company.location AS company_location,
                    cv.title AS cv_title,
                    interview.id AS interview_id,
                    interview.scheduled_at AS interview_scheduled_at,
                    interview.status AS interview_status
                FROM employer_job_applications application
                JOIN employer_jobs job
                    ON job.id = application.job_id
                JOIN employer_companies company
                    ON company.id = application.company_id
                LEFT JOIN cvs cv
                    ON cv.id = application.cv_id
                LEFT JOIN LATERAL (
                    SELECT
                        interview_record.id,
                        interview_record.scheduled_at,
                        interview_record.status
                    FROM employer_application_interviews interview_record
                    WHERE
                        interview_record.application_id = application.id
                    ORDER BY interview_record.scheduled_at DESC
                    LIMIT 1
                ) interview ON TRUE
                WHERE {where_clause}
                ORDER BY application.created_at DESC
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


@router.get("/my/applications/{application_id}")
def my_application_detail(
    application_id: UUID,
    user: dict = Depends(get_current_user),
):
    candidate_user_id = str(user["id"])

    application = get_candidate_application(
        application_id,
        candidate_user_id,
    )

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    scheduled_at,
                    duration_minutes,
                    interview_type,
                    meeting_url,
                    location,
                    notes,
                    status,
                    created_at,
                    updated_at
                FROM employer_application_interviews
                WHERE application_id = %s
                  AND candidate_user_id = %s
                ORDER BY scheduled_at DESC
                """,
                (
                    str(application_id),
                    candidate_user_id,
                ),
            )

            interviews = [
                serialize(row)
                for row in cursor.fetchall()
            ]

            cursor.execute(
                """
                SELECT
                    activity_type,
                    from_status,
                    to_status,
                    created_at
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
        "interviews": interviews,
        "activity": activity,
    }


@router.put("/my/applications/{application_id}/withdraw")
def withdraw_application(
    application_id: UUID,
    user: dict = Depends(get_current_user),
):
    candidate_user_id = str(user["id"])

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM employer_job_applications
                WHERE id = %s
                  AND candidate_user_id = %s
                LIMIT 1
                """,
                (
                    str(application_id),
                    candidate_user_id,
                ),
            )

            current = cursor.fetchone()

            if not current:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Application not found.",
                )

            if current["status"] == "withdrawn":
                return {
                    "message": "Application is already withdrawn.",
                    "application": serialize(current),
                    "changed": False,
                }

            if current["status"] in {
                "hired",
                "rejected",
            }:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "This application can no longer be withdrawn."
                    ),
                )

            cursor.execute(
                """
                UPDATE employer_job_applications
                SET
                    status = 'withdrawn',
                    last_activity_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                  AND candidate_user_id = %s
                RETURNING *
                """,
                (
                    str(application_id),
                    candidate_user_id,
                ),
            )

            updated = cursor.fetchone()

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
                    candidate_user_id,
                    "application_withdrawn",
                    current["status"],
                    "withdrawn",
                    Jsonb({}),
                ),
            )

        connection.commit()

    return {
        "message": "Application withdrawn successfully.",
        "application": serialize(updated),
        "changed": True,
    }