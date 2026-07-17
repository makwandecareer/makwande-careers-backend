from __future__ import annotations

from pydantic import BaseModel, Field


class CareerRoadmapRequest(BaseModel):
    target_role: str = Field(min_length=2, max_length=160)
    timeframe_months: int = Field(default=12, ge=1, le=60)
    country: str = Field(default="South Africa", max_length=120)


class RoadmapStage(BaseModel):
    stage: str
    timeframe: str
    objective: str
    actions: list[str]
    evidence_of_progress: list[str]


class CareerRoadmapResponse(BaseModel):
    target_role: str
    current_positioning: str
    priority_gaps: list[str]
    roadmap: list[RoadmapStage]
    recommended_certifications: list[str]
    portfolio_projects: list[str]
    networking_plan: list[str]
    next_30_days: list[str]


class SkillsGapRequest(BaseModel):
    target_role: str = Field(min_length=2, max_length=160)
    job_description: str = Field(default="", max_length=30000)


class SkillGapItem(BaseModel):
    skill: str
    current_level: str
    required_level: str
    priority: str
    recommendation: str


class SkillsGapResponse(BaseModel):
    readiness_score: int = Field(ge=0, le=100)
    strengths: list[str]
    gaps: list[SkillGapItem]
    learning_plan: list[str]
    recommended_projects: list[str]
    keywords_to_add: list[str]


class InterviewPrepRequest(BaseModel):
    target_role: str = Field(min_length=2, max_length=160)
    company_name: str = Field(default="", max_length=200)
    job_description: str = Field(default="", max_length=30000)
    interview_type: str = Field(default="general", max_length=80)


class InterviewQuestion(BaseModel):
    question: str
    why_it_is_asked: str
    answer_framework: str
    sample_answer: str


class InterviewPrepResponse(BaseModel):
    opening_pitch: str
    likely_questions: list[InterviewQuestion]
    technical_topics: list[str]
    questions_to_ask: list[str]
    preparation_checklist: list[str]
    risk_flags: list[str]


class CoverLetterRequest(BaseModel):
    target_role: str = Field(min_length=2, max_length=160)
    company_name: str = Field(min_length=2, max_length=200)
    job_description: str = Field(default="", max_length=30000)
    tone: str = Field(default="professional", max_length=40)


class CoverLetterResponse(BaseModel):
    subject_line: str
    cover_letter: str
    key_alignment_points: list[str]


class ImproveSummaryRequest(BaseModel):
    target_role: str = Field(default="", max_length=160)
    current_summary: str = Field(default="", max_length=5000)
    tone: str = Field(default="professional", max_length=40)


class ImproveSummaryResponse(BaseModel):
    improved_summary: str
    strengths_added: list[str]
    keywords_added: list[str]


class ImproveExperienceRequest(BaseModel):
    job_title: str = Field(min_length=2, max_length=160)
    company: str = Field(default="", max_length=200)
    current_description: str = Field(min_length=2, max_length=10000)
    target_role: str = Field(default="", max_length=160)


class ImproveExperienceResponse(BaseModel):
    professional_description: str
    achievement_bullets: list[str]
    missing_metrics_to_collect: list[str]
    keywords_added: list[str]


class JobMatchRequest(BaseModel):
    job_description: str = Field(min_length=20, max_length=30000)


class JobMatchResponse(BaseModel):
    match_score: int = Field(ge=0, le=100)
    strong_matches: list[str]
    missing_requirements: list[str]
    transferable_strengths: list[str]
    cv_changes: list[str]
    interview_positioning: list[str]
    recommendation: str
