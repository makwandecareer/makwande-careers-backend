import json
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query

from app.database import get_connection, now_iso, row_to_cv
from app.dependencies import get_current_user
from app.schemas import CVCreate, CVResponse, CVUpdate

router = APIRouter(prefix="/cvs", tags=["CVs"])

@router.post("", response_model=CVResponse, status_code=201)
def create_cv(payload: CVCreate, user: dict = Depends(get_current_user)):
    cv_id = str(uuid4())
    timestamp = now_iso()

    with get_connection() as db:
        db.execute(
            '''
            INSERT INTO cvs (
                id, owner_id, title, target_role, content,
                is_public_to_employers, version, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
            ''',
            (
                cv_id,
                user["id"],
                payload.title,
                payload.target_role,
                json.dumps(payload.content),
                int(payload.is_public_to_employers),
                timestamp,
                timestamp,
            ),
        )
        row = db.execute("SELECT * FROM cvs WHERE id = ?", (cv_id,)).fetchone()

    return row_to_cv(row)

@router.get("", response_model=list[CVResponse])
def list_cvs(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(get_current_user),
):
    with get_connection() as db:
        rows = db.execute(
            '''
            SELECT * FROM cvs
            WHERE owner_id = ?
            ORDER BY updated_at DESC
            LIMIT ? OFFSET ?
            ''',
            (user["id"], limit, offset),
        ).fetchall()

    return [row_to_cv(row) for row in rows]

def get_owned_cv(cv_id: str, user_id: str):
    with get_connection() as db:
        row = db.execute(
            "SELECT * FROM cvs WHERE id = ? AND owner_id = ?",
            (cv_id, user_id),
        ).fetchone()

    cv = row_to_cv(row)
    if cv is None:
        raise HTTPException(status_code=404, detail="CV not found")
    return cv

@router.get("/{cv_id}", response_model=CVResponse)
def get_cv(cv_id: str, user: dict = Depends(get_current_user)):
    return get_owned_cv(cv_id, user["id"])

@router.put("/{cv_id}", response_model=CVResponse)
def update_cv(
    cv_id: str,
    payload: CVUpdate,
    user: dict = Depends(get_current_user),
):
    existing = get_owned_cv(cv_id, user["id"])

    if existing["version"] != payload.version:
        raise HTTPException(
            status_code=409,
            detail="This CV was changed elsewhere. Reload and try again.",
        )

    new_version = payload.version + 1

    with get_connection() as db:
        db.execute(
            '''
            UPDATE cvs
            SET title = ?, target_role = ?, content = ?,
                is_public_to_employers = ?, version = ?, updated_at = ?
            WHERE id = ? AND owner_id = ?
            ''',
            (
                payload.title,
                payload.target_role,
                json.dumps(payload.content),
                int(payload.is_public_to_employers),
                new_version,
                now_iso(),
                cv_id,
                user["id"],
            ),
        )
        row = db.execute("SELECT * FROM cvs WHERE id = ?", (cv_id,)).fetchone()

    return row_to_cv(row)

@router.delete("/{cv_id}", status_code=204)
def delete_cv(cv_id: str, user: dict = Depends(get_current_user)):
    get_owned_cv(cv_id, user["id"])

    with get_connection() as db:
        db.execute(
            "DELETE FROM cvs WHERE id = ? AND owner_id = ?",
            (cv_id, user["id"]),
        )
