import json
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from app.database import get_connection
from app.dependencies import get_current_user
from app.schemas_v4 import (
    CertificationIn,
    LanguageIn,
    ProjectIn,
    ReferenceIn,
)

router = APIRouter()


@router.post("/certifications", status_code=201, tags=["Certifications"])
def add_certification(
    payload: CertificationIn,
    user=Depends(get_current_user),
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO certifications (
                    id,
                    user_id,
                    name,
                    issuer,
                    issue_date,
                    expiry_date,
                    credential_id,
                    credential_url
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    str(uuid4()),
                    user["id"],
                    payload.name,
                    payload.issuer,
                    payload.issue_date,
                    payload.expiry_date,
                    payload.credential_id,
                    payload.credential_url,
                ),
            )
            certification = cursor.fetchone()

        connection.commit()

    return certification


@router.get("/certifications", tags=["Certifications"])
def certifications(user=Depends(get_current_user)):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM certifications
                WHERE user_id=%s
                ORDER BY issue_date DESC NULLS LAST
                """,
                (user["id"],),
            )
            return cursor.fetchall()


@router.post("/projects", status_code=201, tags=["Projects"])
def add_project(
    payload: ProjectIn,
    user=Depends(get_current_user),
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO projects (
                    id,
                    user_id,
                    name,
                    description,
                    project_url,
                    technologies,
                    start_date,
                    end_date
                )
                VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s)
                RETURNING *
                """,
                (
                    str(uuid4()),
                    user["id"],
                    payload.name,
                    payload.description,
                    payload.project_url,
                    json.dumps(payload.technologies),
                    payload.start_date,
                    payload.end_date,
                ),
            )
            project = cursor.fetchone()

        connection.commit()

    return project


@router.get("/projects", tags=["Projects"])
def projects(user=Depends(get_current_user)):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM projects
                WHERE user_id=%s
                ORDER BY start_date DESC NULLS LAST
                """,
                (user["id"],),
            )
            return cursor.fetchall()


@router.post("/languages", status_code=201, tags=["Languages"])
def add_language(
    payload: LanguageIn,
    user=Depends(get_current_user),
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    INSERT INTO languages (
                        id,
                        user_id,
                        name,
                        proficiency
                    )
                    VALUES (%s, %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        str(uuid4()),
                        user["id"],
                        payload.name,
                        payload.proficiency,
                    ),
                )
                language = cursor.fetchone()
            except Exception as exc:
                raise HTTPException(
                    status_code=409,
                    detail="Language already exists",
                ) from exc

        connection.commit()

    return language


@router.get("/languages", tags=["Languages"])
def languages(user=Depends(get_current_user)):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM languages
                WHERE user_id=%s
                ORDER BY name
                """,
                (user["id"],),
            )
            return cursor.fetchall()


@router.post("/references", status_code=201, tags=["References"])
def add_reference(
    payload: ReferenceIn,
    user=Depends(get_current_user),
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO candidate_references (
                    id,
                    user_id,
                    full_name,
                    relationship,
                    company,
                    email,
                    phone
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    str(uuid4()),
                    user["id"],
                    payload.full_name,
                    payload.relationship,
                    payload.company,
                    str(payload.email) if payload.email else None,
                    payload.phone,
                ),
            )
            reference = cursor.fetchone()

        connection.commit()

    return reference


@router.get("/references", tags=["References"])
def references(user=Depends(get_current_user)):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM candidate_references
                WHERE user_id=%s
                ORDER BY full_name
                """,
                (user["id"],),
            )
            return cursor.fetchall()


@router.get("/templates", tags=["CV Templates"])
def templates():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM cv_templates
                WHERE is_active=TRUE
                ORDER BY name
                """
            )
            return cursor.fetchall()