from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.services.ai_cv_analyzer_service import AICVAnalyzerService
from app.services.ai_professional_summary_service import AIProfessionalSummaryService
from app.services.ai_achievement_generator_service import AIAchievementGeneratorService
from app.services.ai_job_description_analyzer_service import AIJobDescriptionAnalyzerService
from app.services.ai_cover_letter_generator_service import AICoverLetterGeneratorService
from app.services.ai_interview_preparation_service import AIInterviewPreparationService
from app.services.ai_career_coach_service import AICareerCoachService

router = APIRouter(prefix="/ai", tags=["AI"])

class AnalyzeRequest(BaseModel):
    draft: dict

class SummaryRequest(BaseModel):
    profile: dict
    experience: list[dict]
    target_role: str | None = None

class AchievementRequest(BaseModel):
    responsibilities: list[str]
    metrics: dict | None = None

class JobMatchRequest(BaseModel):
    job_description: str
    cv_text: str

class CoverLetterRequest(BaseModel):
    profile: dict
    company_name: str
    job_title: str
    job_description: str = ""

class InterviewRequest(BaseModel):
    profile: dict
    job_title: str
    industry: str | None = None
    skills: list[str] = []

class CareerCoachRequest(BaseModel):
    profile: dict
    experience: list[dict]
    skills: list[str]
    target_role: str | None = None

@router.post("/analyze-cv")
def analyze(req: AnalyzeRequest):
    return AICVAnalyzerService().analyse(type("Draft",(object,),req.draft)())

@router.post("/generate-summary")
def summary(req: SummaryRequest):
    return AIProfessionalSummaryService().generate(req.profile, req.experience, req.target_role)

@router.post("/generate-achievements")
def achievements(req: AchievementRequest):
    return AIAchievementGeneratorService().generate(req.responsibilities, req.metrics)

@router.post("/job-match")
def job_match(req: JobMatchRequest):
    return AIJobDescriptionAnalyzerService().analyze(req.job_description, req.cv_text)

@router.post("/cover-letter")
def cover(req: CoverLetterRequest):
    return AICoverLetterGeneratorService().generate(req.profile, req.company_name, req.job_title, req.job_description)

@router.post("/interview-prep")
def interview(req: InterviewRequest):
    return AIInterviewPreparationService().generate(req.profile, req.job_title, req.industry, req.skills)

@router.post("/career-coach")
def coach(req: CareerCoachRequest):
    return AICareerCoachService().advise(req.profile, req.experience, req.skills, req.target_role)
