import re
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from app.database import get_connection
from app.dependencies import get_current_user
from app.schemas_ai_cv import ATSScoreRequest, ATSScoreResponse, ExportCVRequest, GenerateCVRequest, GeneratedCVResponse, ImproveExperienceRequest, ImproveSummaryRequest, TextImprovementResponse
from app.services.cv_builder import build_generated_cv, calculate_ats_score, export_docx, export_pdf, improve_experience, improve_summary

router=APIRouter(prefix="/ai-cv",tags=["AI CV Builder"])

@router.post("/generate",response_model=GeneratedCVResponse)
def generate_cv(payload:GenerateCVRequest,user:dict=Depends(get_current_user)):
    with get_connection() as c:
        with c.cursor() as cur:
            cur.execute("SELECT * FROM profiles WHERE user_id=%s",(user["id"],)); profile=cur.fetchone()
            cur.execute("SELECT * FROM education WHERE user_id=%s ORDER BY start_date DESC NULLS LAST",(user["id"],)); education=cur.fetchall()
            cur.execute("SELECT * FROM experience WHERE user_id=%s ORDER BY start_date DESC NULLS LAST",(user["id"],)); experience=cur.fetchall()
            cur.execute("SELECT * FROM skills WHERE user_id=%s ORDER BY name",(user["id"],)); skills=cur.fetchall()
    return build_generated_cv(user=user,profile=profile,education=education,experience=experience,skills=skills,target_role=payload.target_role,template_key=payload.template_key)

@router.post("/ats-score",response_model=ATSScoreResponse)
def ats_score(payload:ATSScoreRequest,_user:dict=Depends(get_current_user)):
    return calculate_ats_score(payload.cv_content,payload.job_description)

@router.post("/improve-summary",response_model=TextImprovementResponse)
def improve_cv_summary(payload:ImproveSummaryRequest,_user:dict=Depends(get_current_user)):
    return improve_summary(target_role=payload.target_role,current_summary=payload.current_summary,verified_strengths=payload.verified_strengths)

@router.post("/improve-experience",response_model=TextImprovementResponse)
def improve_cv_experience(payload:ImproveExperienceRequest,_user:dict=Depends(get_current_user)):
    return improve_experience(job_title=payload.job_title,duties=payload.duties,verified_achievements=payload.verified_achievements)

@router.post("/export/docx")
def download_docx(payload:ExportCVRequest,_user:dict=Depends(get_current_user)):
    name=_safe(payload.filename)+".docx"
    return Response(content=export_docx(payload.cv_content),media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",headers={"Content-Disposition":f'attachment; filename="{name}"'})

@router.post("/export/pdf")
def download_pdf(payload:ExportCVRequest,_user:dict=Depends(get_current_user)):
    name=_safe(payload.filename)+".pdf"
    return Response(content=export_pdf(payload.cv_content),media_type="application/pdf",headers={"Content-Disposition":f'attachment; filename="{name}"'})

def _safe(value:str)->str:
    cleaned=re.sub(r"[^a-zA-Z0-9_-]+","-",value.strip()).strip("-")
    if not cleaned: raise HTTPException(status_code=422,detail="Invalid filename")
    return cleaned[:100]
