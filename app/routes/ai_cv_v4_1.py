from __future__ import annotations

import json
import re
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from app.database import get_connection
from app.dependencies import get_current_user
from app.schemas_ai_cv_v4_1 import (
    ATSScoreRequest,
    ATSScoreResponse,
    ExportCVRequest,
    GenerateCVRequest,
    GeneratedCVResponse,
    ImproveExperienceRequest,
    ImproveSummaryRequest,
    RevisionAcceptRequest,
    TextImprovementResponse,
)
from app.services.cv_builder_v4_1 import (
    calculate_ats,
    export_docx,
    export_pdf,
    improve_experience_text,
    improve_summary_text,
)

router = APIRouter(prefix="/ai-cv", tags=["AI CV Builder"])


@router.post("/generate", response_model=GeneratedCVResponse)
def generate_cv(payload: GenerateCVRequest, user=Depends(get_current_user)):
    content = _build_structured_content(user)
    title = f"{user['full_name']} - {payload.target_role} CV"

    snapshot_id = None
    if payload.save_snapshot:
        snapshot_id = str(uuid4())
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    '''
                    INSERT INTO generated_cv_snapshots (
                        id,user_id,cv_id,title,target_role,template_key,content
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb)
                    ''',
                    (
                        snapshot_id, user["id"], payload.cv_id, title,
                        payload.target_role, payload.template_key,
                        json.dumps(content, default=str),
                    ),
                )
            connection.commit()

    return GeneratedCVResponse(
        title=title,
        target_role=payload.target_role,
        template_key=payload.template_key,
        content=content,
        warnings=[
            "Review all generated content before publishing.",
            "The CV was assembled only from saved user records.",
        ],
        snapshot_id=snapshot_id,
    )


@router.post("/ats-score", response_model=ATSScoreResponse)
def ats_score(payload: ATSScoreRequest, user=Depends(get_current_user)):
    result = calculate_ats(payload.cv_content, payload.job_description)

    if payload.save_history:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    '''
                    INSERT INTO ats_assessments (
                        id,user_id,cv_id,target_role,job_description,score,
                        matched_keywords,missing_keywords,recommendations
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb)
                    ''',
                    (
                        str(uuid4()), user["id"], payload.cv_id, payload.target_role,
                        payload.job_description, result["score"],
                        json.dumps(result["matched_keywords"]),
                        json.dumps(result["missing_keywords"]),
                        json.dumps(result["recommendations"]),
                    ),
                )
            connection.commit()

    return ATSScoreResponse(**result)


@router.get("/ats-history")
def ats_history(
    limit: int = Query(default=20, ge=1, le=100),
    user=Depends(get_current_user),
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                SELECT *
                FROM ats_assessments
                WHERE user_id=%s
                ORDER BY created_at DESC
                LIMIT %s
                ''',
                (user["id"], limit),
            )
            return cursor.fetchall()


@router.post("/improve-summary", response_model=TextImprovementResponse)
def improve_summary(payload: ImproveSummaryRequest, user=Depends(get_current_user)):
    text, warnings = improve_summary_text(
        payload.target_role,
        payload.current_summary,
        payload.verified_strengths,
    )

    revision_id = None
    if payload.save_revision:
        revision_id = _save_revision(
            user_id=user["id"],
            cv_id=payload.cv_id,
            revision_type="summary",
            source_text=payload.current_summary,
            generated_text=text,
            target_role=payload.target_role,
            warnings=warnings,
        )

    return TextImprovementResponse(
        text=text,
        warnings=warnings,
        revision_id=revision_id,
    )


@router.post("/improve-experience", response_model=TextImprovementResponse)
def improve_experience(payload: ImproveExperienceRequest, user=Depends(get_current_user)):
    text, warnings = improve_experience_text(
        payload.job_title,
        payload.duties,
        payload.verified_achievements,
    )

    revision_id = None
    if payload.save_revision:
        source_text = "\n".join(payload.duties + payload.verified_achievements)
        revision_id = _save_revision(
            user_id=user["id"],
            cv_id=payload.cv_id,
            revision_type="experience",
            source_text=source_text,
            generated_text=text,
            target_role=payload.target_role,
            warnings=warnings,
        )

    return TextImprovementResponse(
        text=text,
        warnings=warnings,
        revision_id=revision_id,
    )


@router.get("/revisions")
def revisions(
    limit: int = Query(default=30, ge=1, le=100),
    user=Depends(get_current_user),
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                SELECT *
                FROM ai_revisions
                WHERE user_id=%s
                ORDER BY created_at DESC
                LIMIT %s
                ''',
                (user["id"], limit),
            )
            return cursor.fetchall()


@router.put("/revisions/{revision_id}/accept")
def accept_revision(
    revision_id: str,
    payload: RevisionAcceptRequest,
    user=Depends(get_current_user),
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                UPDATE ai_revisions
                SET accepted=%s
                WHERE id=%s AND user_id=%s
                RETURNING *
                ''',
                (payload.accepted, revision_id, user["id"]),
            )
            row = cursor.fetchone()
        connection.commit()

    if row is None:
        raise HTTPException(status_code=404, detail="Revision not found")
    return row


@router.get("/generated-history")
def generated_history(
    limit: int = Query(default=20, ge=1, le=100),
    user=Depends(get_current_user),
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                SELECT *
                FROM generated_cv_snapshots
                WHERE user_id=%s
                ORDER BY created_at DESC
                LIMIT %s
                ''',
                (user["id"], limit),
            )
            return cursor.fetchall()


@router.post("/export/docx")
def download_docx(payload: ExportCVRequest, _user=Depends(get_current_user)):
    filename = _safe_filename(payload.filename) + ".docx"
    content = export_docx(payload.cv_content, payload.template_key)

    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/export/pdf")
def download_pdf(payload: ExportCVRequest, _user=Depends(get_current_user)):
    filename = _safe_filename(payload.filename) + ".pdf"
    content = export_pdf(payload.cv_content, payload.template_key)

    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _build_structured_content(user: dict) -> dict:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM profiles WHERE user_id=%s", (user["id"],))
            profile = cursor.fetchone() or {}

            cursor.execute(
                "SELECT * FROM education WHERE user_id=%s ORDER BY start_date DESC NULLS LAST",
                (user["id"],),
            )
            education = cursor.fetchall()

            cursor.execute(
                "SELECT * FROM experience WHERE user_id=%s ORDER BY start_date DESC NULLS LAST",
                (user["id"],),
            )
            experience = cursor.fetchall()

            cursor.execute(
                "SELECT * FROM skills WHERE user_id=%s ORDER BY name",
                (user["id"],),
            )
            skills = cursor.fetchall()

            cursor.execute(
                "SELECT * FROM projects WHERE user_id=%s ORDER BY start_date DESC NULLS LAST",
                (user["id"],),
            )
            projects = cursor.fetchall()

            cursor.execute(
                "SELECT * FROM certifications WHERE user_id=%s ORDER BY issue_date DESC NULLS LAST",
                (user["id"],),
            )
            certifications = cursor.fetchall()

            cursor.execute(
                "SELECT * FROM languages WHERE user_id=%s ORDER BY name",
                (user["id"],),
            )
            languages = cursor.fetchall()

    return {
        "personal_details": {
            "full_name": user["full_name"],
            "email": user["email"],
            "phone": profile.get("phone"),
            "location": profile.get("location"),
            "linkedin_url": profile.get("linkedin_url"),
            "portfolio_url": profile.get("portfolio_url"),
            "website_url": profile.get("website_url"),
        },
        "professional_title": profile.get("professional_title"),
        "professional_summary": profile.get("professional_summary"),
        "skills": skills,
        "experience": experience,
        "education": education,
        "projects": projects,
        "certifications": certifications,
        "languages": languages,
        "references": "Available upon request",
    }


def _save_revision(
    *,
    user_id: str,
    cv_id: str | None,
    revision_type: str,
    source_text: str,
    generated_text: str,
    target_role: str | None,
    warnings: list[str],
) -> str:
    revision_id = str(uuid4())

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                INSERT INTO ai_revisions (
                    id,user_id,cv_id,revision_type,source_text,
                    generated_text,target_role,warnings
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
                ''',
                (
                    revision_id, user_id, cv_id, revision_type,
                    source_text, generated_text, target_role,
                    json.dumps(warnings),
                ),
            )
        connection.commit()

    return revision_id


def _safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-")
    if not cleaned:
        raise HTTPException(status_code=422, detail="Invalid filename")
    return cleaned[:100]
