from typing import Any,Literal
from fastapi import APIRouter,Depends
from pydantic import BaseModel,Field
from app.services.integration_auth import current_user_id
from app.services.subscription_service import require_active_access
from app.services.openai_career_service import generate_json

router=APIRouter(prefix="/ai",tags=["OpenAI Career Engine"])

class Candidate(BaseModel):
    full_name:str|None=None
    target_role:str|None=None
    professional_summary:str|None=None
    experience:list[dict[str,Any]]=Field(default_factory=list)
    education:list[dict[str,Any]]=Field(default_factory=list)
    skills:list[str]=Field(default_factory=list)
    projects:list[dict[str,Any]]=Field(default_factory=list)
class Rewrite(BaseModel):
    section:Literal["summary","experience"]
    current_text:str
    job_description:str|None=None
    candidate:Candidate
class Cover(BaseModel):
    company_name:str|None=None
    job_description:str
    candidate:Candidate
class Review(BaseModel):
    job_description:str|None=None
    candidate:Candidate
class Copilot(BaseModel):
    question:str
    candidate:Candidate

def paid(user_id:str=Depends(current_user_id)):
    require_active_access(user_id); return user_id

@router.post("/resume/rewrite")
async def rewrite(body:Rewrite,user_id:str=Depends(paid)):
    return await generate_json(user_id,f"resume_{body.section}","Return rewritten_text, improvements, missing_evidence and integrity_note.",body.model_dump())
@router.post("/cover-letter")
async def cover(body:Cover,user_id:str=Depends(paid)):
    return await generate_json(user_id,"cover_letter","Return subject, cover_letter, recruiter_message and candidate_confirmation_items.",body.model_dump())
@router.post("/recruiter-review")
async def review(body:Review,user_id:str=Depends(paid)):
    return await generate_json(user_id,"recruiter_review","Return executive_summary, strengths, concerns, interview_questions, priority_actions and readiness_label. No hiring probability.",body.model_dump())
@router.post("/career-copilot")
async def copilot(body:Copilot,user_id:str=Depends(paid)):
    return await generate_json(user_id,"career_copilot","Return answer, recommended_actions, questions_for_candidate and evidence_used.",body.model_dump())
