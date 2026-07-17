from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field

from app.database import get_connection
from app.dependencies import get_current_user


router = APIRouter(prefix="/cv-studio", tags=["CV Studio"])


class CVStudioPayload(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    target_role: str | None = Field(default=None, max_length=160)
    template_key: str = Field(default="ats-standard", max_length=80)
    content: dict[str, Any] = Field(default_factory=dict)


class RenameCVPayload(BaseModel):
    title: str = Field(min_length=1, max_length=160)


def _owner_id(user: dict) -> str:
    return str(user["id"])


@router.get("")
def list_cvs(user: dict = Depends(get_current_user)):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    title,
                    target_role,
                    template_key,
                    content,
                    is_public_to_employers,
                    version,
                    created_at,
                    updated_at
                FROM cvs
                WHERE owner_id = %s
                ORDER BY updated_at DESC, created_at DESC
                """,
                (_owner_id(user),),
            )
            rows = cursor.fetchall()

    return rows


@router.post("", status_code=status.HTTP_201_CREATED)
def create_cv(
    payload: CVStudioPayload,
    user: dict = Depends(get_current_user),
):
    cv_id = uuid4()

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
                    version,
                    created_at,
                    updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s::jsonb, 1, NOW(), NOW())
                RETURNING *
                """,
                (
                    cv_id,
                    _owner_id(user),
                    payload.title,
                    payload.target_role,
                    payload.template_key,
                    __import__("json").dumps(payload.content),
                ),
            )
            created = cursor.fetchone()

        connection.commit()

    return created


@router.get("/{cv_id}")
def get_cv(
    cv_id: UUID,
    user: dict = Depends(get_current_user),
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM cvs
                WHERE id = %s AND owner_id = %s
                """,
                (cv_id, _owner_id(user)),
            )
            row = cursor.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="CV not found")

    return row


@router.put("/{cv_id}")
def update_cv(
    cv_id: UUID,
    payload: CVStudioPayload,
    user: dict = Depends(get_current_user),
):
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
                    version = version + 1,
                    updated_at = NOW()
                WHERE id = %s AND owner_id = %s
                RETURNING *
                """,
                (
                    payload.title,
                    payload.target_role,
                    payload.template_key,
                    __import__("json").dumps(payload.content),
                    cv_id,
                    _owner_id(user),
                ),
            )
            updated = cursor.fetchone()

        connection.commit()

    if updated is None:
        raise HTTPException(status_code=404, detail="CV not found")

    return updated


@router.patch("/{cv_id}/rename")
def rename_cv(
    cv_id: UUID,
    payload: RenameCVPayload,
    user: dict = Depends(get_current_user),
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE cvs
                SET title = %s, updated_at = NOW()
                WHERE id = %s AND owner_id = %s
                RETURNING *
                """,
                (payload.title, cv_id, _owner_id(user)),
            )
            updated = cursor.fetchone()

        connection.commit()

    if updated is None:
        raise HTTPException(status_code=404, detail="CV not found")

    return updated


@router.post("/{cv_id}/duplicate", status_code=status.HTTP_201_CREATED)
def duplicate_cv(
    cv_id: UUID,
    user: dict = Depends(get_current_user),
):
    new_id = uuid4()

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
                    is_public_to_employers,
                    version,
                    created_at,
                    updated_at
                )
                SELECT
                    %s,
                    owner_id,
                    LEFT(title || ' Copy', 160),
                    target_role,
                    template_key,
                    content,
                    FALSE,
                    1,
                    NOW(),
                    NOW()
                FROM cvs
                WHERE id = %s AND owner_id = %s
                RETURNING *
                """,
                (new_id, cv_id, _owner_id(user)),
            )
            duplicated = cursor.fetchone()

        connection.commit()

    if duplicated is None:
        raise HTTPException(status_code=404, detail="CV not found")

    return duplicated


@router.post("/{cv_id}/versions", status_code=status.HTTP_201_CREATED)
def create_version(
    cv_id: UUID,
    user: dict = Depends(get_current_user),
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM cvs
                WHERE id = %s AND owner_id = %s
                """,
                (cv_id, _owner_id(user)),
            )
            cv = cursor.fetchone()

            if cv is None:
                raise HTTPException(status_code=404, detail="CV not found")

            cursor.execute(
                """
                SELECT COALESCE(MAX(version), 0) + 1 AS next_version
                FROM cv_versions
                WHERE cv_id = %s
                """,
                (cv_id,),
            )
            next_version = cursor.fetchone()["next_version"]

            cursor.execute(
                """
                INSERT INTO cv_versions (
                    id,
                    cv_id,
                    owner_id,
                    version,
                    title,
                    target_role,
                    template_key,
                    content,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, NOW())
                RETURNING *
                """,
                (
                    uuid4(),
                    cv_id,
                    _owner_id(user),
                    next_version,
                    cv["title"],
                    cv.get("target_role"),
                    cv["template_key"],
                    __import__("json").dumps(cv["content"]),
                ),
            )
            version = cursor.fetchone()

        connection.commit()

    return version


@router.get("/{cv_id}/versions")
def list_versions(
    cv_id: UUID,
    user: dict = Depends(get_current_user),
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM cv_versions
                WHERE cv_id = %s AND owner_id = %s
                ORDER BY version DESC
                """,
                (cv_id, _owner_id(user)),
            )
            rows = cursor.fetchall()

    return rows


@router.post("/{cv_id}/versions/{version_id}/restore")
def restore_version(
    cv_id: UUID,
    version_id: UUID,
    user: dict = Depends(get_current_user),
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM cv_versions
                WHERE id = %s AND cv_id = %s AND owner_id = %s
                """,
                (version_id, cv_id, _owner_id(user)),
            )
            version = cursor.fetchone()

            if version is None:
                raise HTTPException(status_code=404, detail="CV version not found")

            cursor.execute(
                """
                UPDATE cvs
                SET
                    title = %s,
                    target_role = %s,
                    template_key = %s,
                    content = %s::jsonb,
                    version = version + 1,
                    updated_at = NOW()
                WHERE id = %s AND owner_id = %s
                RETURNING *
                """,
                (
                    version["title"],
                    version.get("target_role"),
                    version["template_key"],
                    __import__("json").dumps(version["content"]),
                    cv_id,
                    _owner_id(user),
                ),
            )
            restored = cursor.fetchone()

        connection.commit()

    return restored


@router.delete("/{cv_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cv(
    cv_id: UUID,
    user: dict = Depends(get_current_user),
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM cvs
                WHERE id = %s AND owner_id = %s
                RETURNING id
                """,
                (cv_id, _owner_id(user)),
            )
            deleted = cursor.fetchone()

        connection.commit()

    if deleted is None:
        raise HTTPException(status_code=404, detail="CV not found")

    return Response(status_code=status.HTTP_204_NO_CONTENT)
