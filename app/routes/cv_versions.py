from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from psycopg import Error as PsycopgError

from app.database import get_connection
from app.dependencies import get_current_user


router = APIRouter(
    prefix="/cvs",
    tags=["CV Autosave and Version History"],
)


# ============================================================
# REQUEST SCHEMAS
# ============================================================


class CVCreateRequest(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=160,
    )

    target_role: str | None = Field(
        default=None,
        max_length=160,
    )

    template_key: str = Field(
        default="real-01",
        max_length=120,
    )

    content: dict[str, Any] = Field(
        default_factory=dict,
    )


class CVUpdateRequest(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=160,
    )

    target_role: str | None = Field(
        default=None,
        max_length=160,
    )

    template_key: str | None = Field(
        default=None,
        max_length=120,
    )

    content: dict[str, Any] | None = None


class CVDuplicateRequest(BaseModel):
    title: str | None = Field(
        default=None,
        max_length=160,
    )


# ============================================================
# HELPERS
# ============================================================


def parse_uuid(
    value: str,
    field_name: str,
) -> UUID:
    try:
        return UUID(str(value))

    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid {field_name}",
        ) from exc


def get_user_id(user: dict[str, Any]) -> UUID:
    user_id = user.get("id")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user ID is missing",
        )

    return parse_uuid(
        str(user_id),
        "user ID",
    )


def create_version_snapshot(
    cursor,
    cv: dict[str, Any],
) -> None:
    cursor.execute(
        """
        INSERT INTO cv_versions (
            id,
            cv_id,
            owner_id,
            version_number,
            title,
            target_role,
            template_key,
            content,
            created_at
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            NOW()
        )
        """,
        (
            uuid4(),
            cv["id"],
            cv["owner_id"],
            cv["version"],
            cv["title"],
            cv.get("target_role"),
            cv["template_key"],
            cv["content"],
        ),
    )


def get_owned_cv(
    cursor,
    cv_id: UUID,
    owner_id: UUID,
) -> dict[str, Any]:
    cursor.execute(
        """
        SELECT *
        FROM cvs
        WHERE id = %s
          AND owner_id = %s
        """,
        (
            cv_id,
            owner_id,
        ),
    )

    cv = cursor.fetchone()

    if cv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV not found",
        )

    return cv


# ============================================================
# CREATE CV
# ============================================================


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
def create_cv(
    payload: CVCreateRequest,
    user: dict[str, Any] = Depends(get_current_user),
):
    owner_id = get_user_id(user)
    cv_id = uuid4()

    try:
        with get_connection() as connection:
            try:
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
                        VALUES (
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            1,
                            NOW(),
                            NOW()
                        )
                        RETURNING *
                        """,
                        (
                            cv_id,
                            owner_id,
                            payload.title.strip(),
                            (
                                payload.target_role.strip()
                                if payload.target_role
                                else None
                            ),
                            payload.template_key,
                            payload.content,
                        ),
                    )

                    created = cursor.fetchone()

                    if created is None:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="CV could not be created",
                        )

                    create_version_snapshot(
                        cursor,
                        created,
                    )

                connection.commit()

                return created

            except Exception:
                connection.rollback()
                raise

    except HTTPException:
        raise

    except PsycopgError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while creating CV: {exc}",
        ) from exc


# ============================================================
# LIST CVS
# ============================================================


@router.get("")
def list_cvs(
    user: dict[str, Any] = Depends(get_current_user),
):
    owner_id = get_user_id(user)

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT *
                    FROM cvs
                    WHERE owner_id = %s
                    ORDER BY updated_at DESC
                    """,
                    (owner_id,),
                )

                return cursor.fetchall()

    except PsycopgError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while loading CVs: {exc}",
        ) from exc


# ============================================================
# GET ONE CV
# ============================================================


@router.get("/{cv_id}")
def get_cv(
    cv_id: str,
    user: dict[str, Any] = Depends(get_current_user),
):
    owner_id = get_user_id(user)
    parsed_cv_id = parse_uuid(
        cv_id,
        "CV ID",
    )

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                return get_owned_cv(
                    cursor,
                    parsed_cv_id,
                    owner_id,
                )

    except HTTPException:
        raise

    except PsycopgError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while loading CV: {exc}",
        ) from exc


# ============================================================
# UPDATE / AUTOSAVE CV
# ============================================================


@router.put("/{cv_id}")
def update_cv(
    cv_id: str,
    payload: CVUpdateRequest,
    user: dict[str, Any] = Depends(get_current_user),
):
    owner_id = get_user_id(user)
    parsed_cv_id = parse_uuid(
        cv_id,
        "CV ID",
    )

    changes = payload.model_dump(
        exclude_unset=True,
    )

    if not changes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No changes supplied",
        )

    allowed_fields = [
        "title",
        "target_role",
        "template_key",
        "content",
    ]

    update_fields = [
        field
        for field in allowed_fields
        if field in changes
    ]

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No valid CV fields supplied",
        )

    assignments = ", ".join(
        f"{field} = %s"
        for field in update_fields
    )

    values = [
        changes[field]
        for field in update_fields
    ]

    try:
        with get_connection() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"""
                        UPDATE cvs
                        SET
                            {assignments},
                            version = version + 1,
                            updated_at = NOW()
                        WHERE id = %s
                          AND owner_id = %s
                        RETURNING *
                        """,
                        (
                            *values,
                            parsed_cv_id,
                            owner_id,
                        ),
                    )

                    updated = cursor.fetchone()

                    if updated is None:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="CV not found",
                        )

                    create_version_snapshot(
                        cursor,
                        updated,
                    )

                connection.commit()

                return updated

            except Exception:
                connection.rollback()
                raise

    except HTTPException:
        raise

    except PsycopgError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while updating CV: {exc}",
        ) from exc


# ============================================================
# DELETE CV
# ============================================================


@router.delete(
    "/{cv_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_cv(
    cv_id: str,
    user: dict[str, Any] = Depends(get_current_user),
):
    owner_id = get_user_id(user)
    parsed_cv_id = parse_uuid(
        cv_id,
        "CV ID",
    )

    try:
        with get_connection() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        DELETE FROM cvs
                        WHERE id = %s
                          AND owner_id = %s
                        RETURNING id
                        """,
                        (
                            parsed_cv_id,
                            owner_id,
                        ),
                    )

                    deleted = cursor.fetchone()

                    if deleted is None:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="CV not found",
                        )

                connection.commit()

            except Exception:
                connection.rollback()
                raise

    except HTTPException:
        raise

    except PsycopgError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while deleting CV: {exc}",
        ) from exc

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


# ============================================================
# DUPLICATE CV
# ============================================================


@router.post(
    "/{cv_id}/duplicate",
    status_code=status.HTTP_201_CREATED,
)
def duplicate_cv(
    cv_id: str,
    payload: CVDuplicateRequest,
    user: dict[str, Any] = Depends(get_current_user),
):
    owner_id = get_user_id(user)
    parsed_cv_id = parse_uuid(
        cv_id,
        "CV ID",
    )
    new_cv_id = uuid4()

    try:
        with get_connection() as connection:
            try:
                with connection.cursor() as cursor:
                    source = get_owned_cv(
                        cursor,
                        parsed_cv_id,
                        owner_id,
                    )

                    duplicate_title = (
                        payload.title.strip()
                        if payload.title
                        else f'{source["title"]} Copy'
                    )

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
                        VALUES (
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            1,
                            NOW(),
                            NOW()
                        )
                        RETURNING *
                        """,
                        (
                            new_cv_id,
                            owner_id,
                            duplicate_title,
                            source.get("target_role"),
                            source["template_key"],
                            source["content"],
                        ),
                    )

                    duplicated = cursor.fetchone()

                    if duplicated is None:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="CV could not be duplicated",
                        )

                    create_version_snapshot(
                        cursor,
                        duplicated,
                    )

                connection.commit()

                return duplicated

            except Exception:
                connection.rollback()
                raise

    except HTTPException:
        raise

    except PsycopgError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while duplicating CV: {exc}",
        ) from exc


# ============================================================
# LIST VERSION HISTORY
# ============================================================


@router.get("/{cv_id}/versions")
def list_cv_versions(
    cv_id: str,
    user: dict[str, Any] = Depends(get_current_user),
):
    owner_id = get_user_id(user)
    parsed_cv_id = parse_uuid(
        cv_id,
        "CV ID",
    )

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                get_owned_cv(
                    cursor,
                    parsed_cv_id,
                    owner_id,
                )

                cursor.execute(
                    """
                    SELECT *
                    FROM cv_versions
                    WHERE cv_id = %s
                      AND owner_id = %s
                    ORDER BY version_number DESC
                    """,
                    (
                        parsed_cv_id,
                        owner_id,
                    ),
                )

                return cursor.fetchall()

    except HTTPException:
        raise

    except PsycopgError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while loading versions: {exc}",
        ) from exc


# ============================================================
# RESTORE VERSION
# ============================================================


@router.post(
    "/{cv_id}/versions/{version_id}/restore",
)
def restore_cv_version(
    cv_id: str,
    version_id: str,
    user: dict[str, Any] = Depends(get_current_user),
):
    owner_id = get_user_id(user)

    parsed_cv_id = parse_uuid(
        cv_id,
        "CV ID",
    )

    parsed_version_id = parse_uuid(
        version_id,
        "version ID",
    )

    try:
        with get_connection() as connection:
            try:
                with connection.cursor() as cursor:
                    get_owned_cv(
                        cursor,
                        parsed_cv_id,
                        owner_id,
                    )

                    cursor.execute(
                        """
                        SELECT *
                        FROM cv_versions
                        WHERE id = %s
                          AND cv_id = %s
                          AND owner_id = %s
                        """,
                        (
                            parsed_version_id,
                            parsed_cv_id,
                            owner_id,
                        ),
                    )

                    version = cursor.fetchone()

                    if version is None:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="CV version not found",
                        )

                    cursor.execute(
                        """
                        UPDATE cvs
                        SET
                            title = %s,
                            target_role = %s,
                            template_key = %s,
                            content = %s,
                            version = version + 1,
                            updated_at = NOW()
                        WHERE id = %s
                          AND owner_id = %s
                        RETURNING *
                        """,
                        (
                            version["title"],
                            version.get("target_role"),
                            version["template_key"],
                            version["content"],
                            parsed_cv_id,
                            owner_id,
                        ),
                    )

                    restored = cursor.fetchone()

                    if restored is None:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="CV not found",
                        )

                    create_version_snapshot(
                        cursor,
                        restored,
                    )

                connection.commit()

                return restored

            except Exception:
                connection.rollback()
                raise

    except HTTPException:
        raise

    except PsycopgError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while restoring CV version: {exc}",
        ) from exc