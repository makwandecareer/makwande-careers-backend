from fastapi import APIRouter, Depends, Query

from app.database import get_connection, row_to_cv
from app.dependencies import require_roles
from app.schemas import CVResponse

router = APIRouter(prefix="/employers", tags=["Employer Portal"])

@router.get("/candidates", response_model=list[CVResponse])
def list_public_candidates(
    target_role: str | None = Query(default=None, max_length=160),
    limit: int = Query(default=20, ge=1, le=100),
    _user: dict = Depends(require_roles("employer", "admin")),
):
    with get_connection() as db:
        if target_role:
            rows = db.execute(
                '''
                SELECT * FROM cvs
                WHERE is_public_to_employers = 1
                  AND target_role LIKE ?
                ORDER BY updated_at DESC
                LIMIT ?
                ''',
                (f"%{target_role}%", limit),
            ).fetchall()
        else:
            rows = db.execute(
                '''
                SELECT * FROM cvs
                WHERE is_public_to_employers = 1
                ORDER BY updated_at DESC
                LIMIT ?
                ''',
                (limit,),
            ).fetchall()

    return [row_to_cv(row) for row in rows]
