from __future__ import annotations

import json
import logging
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from psycopg import Error as PsycopgError
from psycopg.errors import UniqueViolation

from app.database import get_connection
from app.dependencies import current_user, roles
from app.schemas import (
    CVIn,
    CVUpdate,
    CareerGuidanceIn,
    EducationIn,
    ExperienceIn,
    ProfileIn,
    SkillIn,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Platform"])

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


def _database_error(operation: str, exc: Exception) -> HTTPException:
    logger.exception("Database operation failed: %s", operation, exc_info=exc)
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="The service is temporarily unavailable. Please try again later.",
    )


def _safe_user(user: dict[str, Any]) -> dict[str, Any]:
    blocked_fields = {
        "password_hash",
        "reset_token",
        "reset_token_hash",
    }
    return {
        key: value
        for key, value in user.items()
        if key not in blocked_fields
    }


@router.get(
    "/users/me",
    operation_id="platform_get_current_user",
)
def me(
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    return _safe_user(user)


@router.put(
    "/profile",
    operation_id="platform_upsert_profile",
)
def profile(
    payload: ProfileIn,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO profiles (
                        id,
                        user_id,
                        phone,
                        location,
                        professional_title,
                        professional_summary,
                        linkedin_url,
                        portfolio_url,
                        visibility
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id)
                    DO UPDATE SET
                        phone = EXCLUDED.phone,
                        location = EXCLUDED.location,
                        professional_title = EXCLUDED.professional_title,
                        professional_summary = EXCLUDED.professional_summary,
                        linkedin_url = EXCLUDED.linkedin_url,
                        portfolio_url = EXCLUDED.portfolio_url,
                        visibility = EXCLUDED.visibility,
                        updated_at = NOW()
                    RETURNING *
                    """,
                    (
                        str(uuid4()),
                        user["id"],
                        payload.phone,
                        payload.location,
                        payload.professional_title,
                        payload.professional_summary,
                        payload.linkedin_url,
                        payload.portfolio_url,
                        payload.visibility,
                    ),
                )
                row = cursor.fetchone()
            connection.commit()

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Profile could not be saved.",
            )

        return row
    except HTTPException:
        raise
    except PsycopgError as exc:
        raise _database_error("save profile", exc) from exc


@router.post(
    "/education",
    status_code=status.HTTP_201_CREATED,
    operation_id="platform_add_education",
)
def add_education(
    payload: EducationIn,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO education (
                        id,
                        user_id,
                        institution,
                        qualification,
                        field_of_study,
                        start_date,
                        end_date,
                        description
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        str(uuid4()),
                        user["id"],
                        payload.institution,
                        payload.qualification,
                        payload.field_of_study,
                        payload.start_date,
                        payload.end_date,
                        payload.description,
                    ),
                )
                row = cursor.fetchone()
            connection.commit()

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Education record could not be created.",
            )

        return row
    except HTTPException:
        raise
    except PsycopgError as exc:
        raise _database_error("add education", exc) from exc


@router.get(
    "/education",
    operation_id="platform_list_education",
)
def education(
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(0, ge=0),
    user: dict[str, Any] = Depends(current_user),
) -> list[dict[str, Any]]:
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT *
                    FROM education
                    WHERE user_id = %s
                    ORDER BY start_date DESC NULLS LAST, id DESC
                    LIMIT %s OFFSET %s
                    """,
                    (user["id"], limit, offset),
                )
                return cursor.fetchall()
    except PsycopgError as exc:
        raise _database_error("list education", exc) from exc


@router.post(
    "/experience",
    status_code=status.HTTP_201_CREATED,
    operation_id="platform_add_experience",
)
def add_experience(
    payload: ExperienceIn,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO experience (
                        id,
                        user_id,
                        company,
                        job_title,
                        start_date,
                        end_date,
                        description,
                        achievements
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                    RETURNING *
                    """,
                    (
                        str(uuid4()),
                        user["id"],
                        payload.company,
                        payload.job_title,
                        payload.start_date,
                        payload.end_date,
                        payload.description,
                        json.dumps(payload.achievements or []),
                    ),
                )
                row = cursor.fetchone()
            connection.commit()

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Experience record could not be created.",
            )

        return row
    except HTTPException:
        raise
    except PsycopgError as exc:
        raise _database_error("add experience", exc) from exc


@router.get(
    "/experience",
    operation_id="platform_list_experience",
)
def experience(
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(0, ge=0),
    user: dict[str, Any] = Depends(current_user),
) -> list[dict[str, Any]]:
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT *
                    FROM experience
                    WHERE user_id = %s
                    ORDER BY start_date DESC NULLS LAST, id DESC
                    LIMIT %s OFFSET %s
                    """,
                    (user["id"], limit, offset),
                )
                return cursor.fetchall()
    except PsycopgError as exc:
        raise _database_error("list experience", exc) from exc


@router.post(
    "/skills",
    status_code=status.HTTP_201_CREATED,
    operation_id="platform_add_skill",
)
def add_skill(
    payload: SkillIn,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO skills (
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
                        payload.name.strip(),
                        payload.proficiency,
                    ),
                )
                row = cursor.fetchone()
            connection.commit()

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Skill could not be created.",
            )

        return row
    except UniqueViolation as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Skill already exists.",
        ) from exc
    except HTTPException:
        raise
    except PsycopgError as exc:
        raise _database_error("add skill", exc) from exc


@router.get(
    "/skills",
    operation_id="platform_list_skills",
)
def skills(
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(0, ge=0),
    user: dict[str, Any] = Depends(current_user),
) -> list[dict[str, Any]]:
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT *
                    FROM skills
                    WHERE user_id = %s
                    ORDER BY name ASC
                    LIMIT %s OFFSET %s
                    """,
                    (user["id"], limit, offset),
                )
                return cursor.fetchall()
    except PsycopgError as exc:
        raise _database_error("list skills", exc) from exc


@router.post(
    "/cvs",
    status_code=status.HTTP_201_CREATED,
    operation_id="platform_create_cv",
)
def create_cv(
    payload: CVIn,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO cvs (
                        id,
                        owner_id,
                        title,
                        target_role,
                        template_key,
                        content,
                        is_public_to_employers
                    )
                    VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s)
                    RETURNING *
                    """,
                    (
                        str(uuid4()),
                        user["id"],
                        payload.title,
                        payload.target_role,
                        payload.template_key,
                        json.dumps(payload.content),
                        payload.is_public_to_employers,
                    ),
                )
                row = cursor.fetchone()
            connection.commit()

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="CV could not be created.",
            )

        return row
    except HTTPException:
        raise
    except PsycopgError as exc:
        raise _database_error("create CV", exc) from exc


@router.get(
    "/cvs",
    operation_id="platform_list_cvs",
)
def cvs(
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(0, ge=0),
    user: dict[str, Any] = Depends(current_user),
) -> list[dict[str, Any]]:
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT *
                    FROM cvs
                    WHERE owner_id = %s
                    ORDER BY updated_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (user["id"], limit, offset),
                )
                return cursor.fetchall()
    except PsycopgError as exc:
        raise _database_error("list CVs", exc) from exc


@router.put(
    "/cvs/{cv_id}",
    operation_id="platform_update_cv",
)
def update_cv(
    cv_id: str,
    payload: CVUpdate,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE cvs
                    SET
                        title = %s,
                        target_role = %s,
                        template_key = %s,
                        content = %s::jsonb,
                        is_public_to_employers = %s,
                        version = version + 1,
                        updated_at = NOW()
                    WHERE id = %s
                      AND owner_id = %s
                      AND version = %s
                    RETURNING *
                    """,
                    (
                        payload.title,
                        payload.target_role,
                        payload.template_key,
                        json.dumps(payload.content),
                        payload.is_public_to_employers,
                        cv_id,
                        user["id"],
                        payload.version,
                    ),
                )
                row = cursor.fetchone()

            if row is None:
                connection.rollback()
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="CV not found, access denied, or version conflict.",
                )

            connection.commit()
            return row
    except HTTPException:
        raise
    except PsycopgError as exc:
        raise _database_error("update CV", exc) from exc


@router.get(
    "/employers/candidates",
    operation_id="platform_list_visible_candidates",
)
def candidates(
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(0, ge=0),
    user: dict[str, Any] = Depends(roles("employer", "admin")),
) -> list[dict[str, Any]]:
    del user

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT c.*
                    FROM cvs AS c
                    INNER JOIN profiles AS p
                        ON p.user_id = c.owner_id
                    WHERE c.is_public_to_employers = TRUE
                      AND p.visibility = 'employers'
                    ORDER BY c.updated_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (limit, offset),
                )
                return cursor.fetchall()
    except PsycopgError as exc:
        raise _database_error("list visible candidates", exc) from exc


@router.post(
    "/career/guidance",
    operation_id="platform_generate_career_guidance",
)
def guidance(
    payload: CareerGuidanceIn,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, list[str]]:
    del user

    strengths = payload.skills[:5] or [
        "Profile requires further assessment."
    ]

    return {
        "strengths": strengths,
        "gaps": [
            f"Compare your evidence with current {payload.target_role} requirements."
        ],
        "next_steps": [
            "Review three current job descriptions.",
            "Identify recurring requirements.",
            "Match each requirement to verified evidence.",
            "Build a practical project for the highest-priority gap.",
        ],
    }