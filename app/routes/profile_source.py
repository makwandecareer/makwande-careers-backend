from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Response, status
from psycopg import Error as PsycopgError

from app.database import get_connection
from app.dependencies import get_current_user


logger = logging.getLogger(__name__)

router = APIRouter(tags=["Profile Source of Truth"])


PROFILE_COLUMNS = [
    "phone",
    "location",
    "professional_title",
    "professional_summary",
    "linkedin_url",
    "portfolio_url",
    "website_url",
    "visibility",
]


RESOURCE_CONFIG: dict[str, dict[str, Any]] = {
    "education": {
        "table": "education",
        "fields": [
            "institution",
            "qualification",
            "field_of_study",
            "start_date",
            "end_date",
            "description",
        ],
    },
    "experience": {
        "table": "experience",
        "fields": [
            "company",
            "job_title",
            "start_date",
            "end_date",
            "description",
        ],
    },
    "skills": {
        "table": "skills",
        "fields": [
            "name",
            "proficiency",
        ],
    },
    "projects": {
        "table": "projects",
        "fields": [
            "name",
            "description",
            "project_url",
            "start_date",
            "end_date",
        ],
    },
    "certifications": {
        "table": "certifications",
        "fields": [
            "name",
            "issuer",
            "issue_date",
            "expiry_date",
            "credential_id",
            "credential_url",
        ],
    },
    "languages": {
        "table": "languages",
        "fields": [
            "name",
            "proficiency",
        ],
    },
    "references": {
        "table": "candidate_references",
        "fields": [
            "full_name",
            "relationship",
            "company",
            "email",
            "phone",
        ],
    },
}


def normalise_uuid(value: str, field_name: str) -> UUID:
    try:
        return UUID(value)
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid {field_name}",
        ) from exc


def calculate_completion(
    profile: dict[str, Any] | None,
    collections: dict[str, list[Any]],
) -> dict[str, Any]:
    profile_complete = bool(
        profile
        and profile.get("phone")
        and profile.get("location")
        and profile.get("professional_title")
        and profile.get("professional_summary")
    )

    sections = {
        "profile": profile_complete,
        "education": bool(collections.get("education")),
        "experience": bool(collections.get("experience")),
        "skills": bool(collections.get("skills")),
        "projects": bool(collections.get("projects")),
        "certifications": bool(collections.get("certifications")),
        "languages": bool(collections.get("languages")),
        "references": bool(collections.get("references")),
        "cv": bool(collections.get("cvs")),
    }

    completed = sum(1 for complete in sections.values() if complete)

    return {
        "percentage": round((completed / len(sections)) * 100),
        "sections": sections,
    }


@router.get("/profile")
def get_profile(user: dict = Depends(get_current_user)):
    user_id = normalise_uuid(str(user["id"]), "user ID")

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    phone,
                    location,
                    professional_title,
                    professional_summary,
                    linkedin_url,
                    portfolio_url,
                    website_url,
                    visibility
                FROM profiles
                WHERE user_id = %s
                """,
                (user_id,),
            )
            profile = cursor.fetchone()

    if profile is None:
        return None

    return profile


@router.get("/profile/source-of-truth")
def profile_source_of_truth(
    user: dict = Depends(get_current_user),
):
    user_id = normalise_uuid(str(user["id"]), "user ID")
    collections: dict[str, list[Any]] = {}

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        phone,
                        location,
                        professional_title,
                        professional_summary,
                        linkedin_url,
                        portfolio_url,
                        website_url,
                        visibility
                    FROM profiles
                    WHERE user_id = %s
                    """,
                    (user_id,),
                )
                profile = cursor.fetchone()

                for resource, config in RESOURCE_CONFIG.items():
                    table = config["table"]

                    cursor.execute(
                        f"""
                        SELECT *
                        FROM {table}
                        WHERE user_id = %s
                        ORDER BY created_at DESC
                        """,
                        (user_id,),
                    )
                    collections[resource] = cursor.fetchall()

                cursor.execute(
                    """
                    SELECT *
                    FROM cvs
                    WHERE owner_id = %s
                    ORDER BY created_at DESC
                    """,
                    (user_id,),
                )
                collections["cvs"] = cursor.fetchall()

                cursor.execute(
                    """
                    SELECT *
                    FROM ats_assessments
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    """,
                    (user_id,),
                )
                collections["ats_history"] = cursor.fetchall()

    except PsycopgError as exc:
        logger.exception("Unable to load profile source of truth")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {exc}",
        ) from exc

    return {
        "user": user,
        "profile": profile,
        **collections,
        "completion": calculate_completion(profile, collections),
    }


def update_resource(
    resource: str,
    record_id: str,
    payload: dict[str, Any],
    user: dict,
):
    config = RESOURCE_CONFIG.get(resource)

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unknown resource",
        )

    parsed_record_id = normalise_uuid(record_id, "record ID")
    user_id = normalise_uuid(str(user["id"]), "user ID")

    allowed_fields = config["fields"]
    update_fields = [
        field
        for field in allowed_fields
        if field in payload
    ]

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No valid fields supplied",
        )

    assignments = ", ".join(
        f"{field} = %s"
        for field in update_fields
    )

    values = [
        payload.get(field)
        for field in update_fields
    ]

    table = config["table"]

    try:
        with get_connection() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"""
                        UPDATE {table}
                        SET {assignments}
                        WHERE id = %s
                          AND user_id = %s
                        RETURNING *
                        """,
                        (
                            *values,
                            parsed_record_id,
                            user_id,
                        ),
                    )

                    updated = cursor.fetchone()

                if updated is None:
                    connection.rollback()

                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"{resource.capitalize()} record not found",
                    )

                connection.commit()
                return updated

            except HTTPException:
                raise

            except PsycopgError as exc:
                connection.rollback()
                logger.exception(
                    "Database update failed for %s %s",
                    resource,
                    parsed_record_id,
                )

                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Database update error: {exc}",
                ) from exc

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception(
            "Unexpected update error for %s %s",
            resource,
            parsed_record_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected update error: {exc}",
        ) from exc


def delete_resource(
    resource: str,
    record_id: str,
    user: dict,
):
    config = RESOURCE_CONFIG.get(resource)

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unknown resource",
        )

    parsed_record_id = normalise_uuid(record_id, "record ID")
    user_id = normalise_uuid(str(user["id"]), "user ID")
    table = config["table"]

    try:
        with get_connection() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"""
                        DELETE FROM {table}
                        WHERE id = %s
                          AND user_id = %s
                        RETURNING id
                        """,
                        (
                            parsed_record_id,
                            user_id,
                        ),
                    )

                    deleted = cursor.fetchone()

                if deleted is None:
                    connection.rollback()

                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"{resource.capitalize()} record not found",
                    )

                connection.commit()

            except HTTPException:
                raise

            except PsycopgError as exc:
                connection.rollback()
                logger.exception(
                    "Database delete failed for %s %s",
                    resource,
                    parsed_record_id,
                )

                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Database delete error: {exc}",
                ) from exc

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception(
            "Unexpected delete error for %s %s",
            resource,
            parsed_record_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected delete error: {exc}",
        ) from exc

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


@router.put("/education/{record_id}")
def update_education(
    record_id: str,
    payload: dict[str, Any] = Body(...),
    user: dict = Depends(get_current_user),
):
    return update_resource(
        "education",
        record_id,
        payload,
        user,
    )


@router.delete(
    "/education/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_education(
    record_id: str,
    user: dict = Depends(get_current_user),
):
    return delete_resource(
        "education",
        record_id,
        user,
    )


@router.put("/experience/{record_id}")
def update_experience(
    record_id: str,
    payload: dict[str, Any] = Body(...),
    user: dict = Depends(get_current_user),
):
    return update_resource(
        "experience",
        record_id,
        payload,
        user,
    )


@router.delete(
    "/experience/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_experience(
    record_id: str,
    user: dict = Depends(get_current_user),
):
    return delete_resource(
        "experience",
        record_id,
        user,
    )


@router.put("/skills/{record_id}")
def update_skill(
    record_id: str,
    payload: dict[str, Any] = Body(...),
    user: dict = Depends(get_current_user),
):
    return update_resource(
        "skills",
        record_id,
        payload,
        user,
    )


@router.delete(
    "/skills/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_skill(
    record_id: str,
    user: dict = Depends(get_current_user),
):
    return delete_resource(
        "skills",
        record_id,
        user,
    )


@router.put("/projects/{record_id}")
def update_project(
    record_id: str,
    payload: dict[str, Any] = Body(...),
    user: dict = Depends(get_current_user),
):
    return update_resource(
        "projects",
        record_id,
        payload,
        user,
    )


@router.delete(
    "/projects/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_project(
    record_id: str,
    user: dict = Depends(get_current_user),
):
    return delete_resource(
        "projects",
        record_id,
        user,
    )


@router.put("/certifications/{record_id}")
def update_certification(
    record_id: str,
    payload: dict[str, Any] = Body(...),
    user: dict = Depends(get_current_user),
):
    return update_resource(
        "certifications",
        record_id,
        payload,
        user,
    )


@router.delete(
    "/certifications/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_certification(
    record_id: str,
    user: dict = Depends(get_current_user),
):
    return delete_resource(
        "certifications",
        record_id,
        user,
    )


@router.put("/languages/{record_id}")
def update_language(
    record_id: str,
    payload: dict[str, Any] = Body(...),
    user: dict = Depends(get_current_user),
):
    return update_resource(
        "languages",
        record_id,
        payload,
        user,
    )


@router.delete(
    "/languages/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_language(
    record_id: str,
    user: dict = Depends(get_current_user),
):
    return delete_resource(
        "languages",
        record_id,
        user,
    )


@router.put("/references/{record_id}")
def update_reference(
    record_id: str,
    payload: dict[str, Any] = Body(...),
    user: dict = Depends(get_current_user),
):
    return update_resource(
        "references",
        record_id,
        payload,
        user,
    )


@router.delete(
    "/references/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_reference(
    record_id: str,
    user: dict = Depends(get_current_user),
):
    return delete_resource(
        "references",
        record_id,
        user,
    )