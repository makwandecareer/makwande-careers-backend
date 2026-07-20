from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user
from app.routes.profile_source import profile_source_of_truth
from app.schemas_ai_career import (
    CareerRoadmapRequest,
    CareerRoadmapResponse,
    CoverLetterRequest,
    CoverLetterResponse,
    ImproveExperienceRequest,
    ImproveExperienceResponse,
    ImproveSummaryRequest,
    ImproveSummaryResponse,
    InterviewPrepRequest,
    InterviewPrepResponse,
    JobMatchRequest,
    JobMatchResponse,
    SkillsGapRequest,
    SkillsGapResponse,
)
from app.services.openai_career_engine import CareerEngineError, OpenAICareerEngine


router = APIRouter(prefix="/ai-career", tags=["OpenAI Career Engine"])


def engine() -> OpenAICareerEngine:
    try:
        return OpenAICareerEngine()
    except CareerEngineError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


def profile_bundle(user: dict) -> dict:
    try:
        return profile_source_of_truth(user)
    except TypeError:
        return profile_source_of_truth(user=user)


def run_structured(
    *,
    user: dict,
    schema,
    task: str,
    payload: dict,
):
    try:
        return engine().structured(
            schema=schema,
            task=task,
            profile_bundle=profile_bundle(user),
            request_data=payload,
        )
    except CareerEngineError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@router.post("/roadmap", response_model=CareerRoadmapResponse)
def roadmap(
    request: CareerRoadmapRequest,
    user: dict = Depends(get_current_user),
):
    return run_structured(
        user=user,
        schema=CareerRoadmapResponse,
        task="Create a realistic staged career roadmap.",
        payload=request.model_dump(),
    )


@router.post("/skills-gap", response_model=SkillsGapResponse)
def skills_gap(
    request: SkillsGapRequest,
    user: dict = Depends(get_current_user),
):
    return run_structured(
        user=user,
        schema=SkillsGapResponse,
        task="Assess skills readiness and produce a prioritised gap plan.",
        payload=request.model_dump(),
    )


@router.post("/interview-prep", response_model=InterviewPrepResponse)
def interview_prep(
    request: InterviewPrepRequest,
    user: dict = Depends(get_current_user),
):
    return run_structured(
        user=user,
        schema=InterviewPrepResponse,
        task="Prepare the candidate for the specified interview.",
        payload=request.model_dump(),
    )


@router.post("/cover-letter", response_model=CoverLetterResponse)
def cover_letter(
    request: CoverLetterRequest,
    user: dict = Depends(get_current_user),
):
    return run_structured(
        user=user,
        schema=CoverLetterResponse,
        task="Write a tailored, truthful and concise cover letter.",
        payload=request.model_dump(),
    )


@router.post("/improve-summary", response_model=ImproveSummaryResponse)
def improve_summary(
    request: ImproveSummaryRequest,
    user: dict = Depends(get_current_user),
):
    return run_structured(
        user=user,
        schema=ImproveSummaryResponse,
        task="Rewrite the professional summary for clarity, relevance and ATS alignment.",
        payload=request.model_dump(),
    )


@router.post("/improve-experience", response_model=ImproveExperienceResponse)
def improve_experience(
    request: ImproveExperienceRequest,
    user: dict = Depends(get_current_user),
):
    return run_structured(
        user=user,
        schema=ImproveExperienceResponse,
        task="Rewrite the experience description without inventing facts.",
        payload=request.model_dump(),
    )


@router.post("/job-match", response_model=JobMatchResponse)
def job_match(
    request: JobMatchRequest,
    user: dict = Depends(get_current_user),
):
    return run_structured(
        user=user,
        schema=JobMatchResponse,
        task="Compare the candidate source of truth with the job description.",
        payload=request.model_dump(),
    )
