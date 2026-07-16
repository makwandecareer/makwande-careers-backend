from fastapi import APIRouter, Depends, Query

from app.database import get_connection
from app.dependencies import get_current_user, require_roles
from app.schemas_v6 import (
    CareerRoadmapRequest,
    CoverLetterRequest,
    InterviewPrepRequest,
    JobMatchRequest,
    JobMatchResponse,
    SkillsGapRequest,
)
from app.services.ai_recruiter_v6 import (
    career_roadmap,
    cover_letter,
    interview_questions,
    job_match,
    skills_gap,
)


router = APIRouter(tags=["Version 6"])


@router.get("/dashboard/candidate-v6", tags=["Candidate Dashboard"])
def candidate_dashboard_v6(user=Depends(get_current_user)):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) AS total FROM cvs WHERE owner_id=%s",
                (user["id"],),
            )
            cvs = cursor.fetchone()["total"]

            cursor.execute(
                "SELECT COUNT(*) AS total FROM applications WHERE candidate_user_id=%s",
                (user["id"],),
            )
            applications = cursor.fetchone()["total"]

            cursor.execute(
                "SELECT COUNT(*) AS total FROM saved_jobs WHERE candidate_user_id=%s",
                (user["id"],),
            )
            saved_jobs = cursor.fetchone()["total"]

            cursor.execute(
                "SELECT COUNT(*) AS total FROM interviews WHERE candidate_user_id=%s",
                (user["id"],),
            )
            interviews = cursor.fetchone()["total"]

            cursor.execute(
                "SELECT COUNT(*) AS total FROM notifications WHERE user_id=%s AND is_read=FALSE",
                (user["id"],),
            )
            unread_notifications = cursor.fetchone()["total"]

    return {
        "user": {
            "id": str(user["id"]),
            "full_name": user["full_name"],
            "email": user["email"],
        },
        "counts": {
            "cvs": cvs,
            "applications": applications,
            "saved_jobs": saved_jobs,
            "interviews": interviews,
            "unread_notifications": unread_notifications,
        },
    }


@router.get("/dashboard/employer-v6", tags=["Employer Portal"])
def employer_dashboard_v6(
    user=Depends(require_roles("employer", "admin")),
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM employers WHERE owner_user_id=%s",
                (user["id"],),
            )
            employer = cursor.fetchone()

            if employer is None:
                return {"employer_profile_required": True}

            cursor.execute(
                "SELECT COUNT(*) AS total FROM jobs WHERE employer_id=%s",
                (employer["id"],),
            )
            jobs = cursor.fetchone()["total"]

            cursor.execute(
                '''
                SELECT COUNT(*) AS total
                FROM applications a
                JOIN jobs j ON j.id=a.job_id
                WHERE j.employer_id=%s
                ''',
                (employer["id"],),
            )
            applications = cursor.fetchone()["total"]

            cursor.execute(
                "SELECT COUNT(*) AS total FROM shortlists WHERE employer_id=%s",
                (employer["id"],),
            )
            shortlists = cursor.fetchone()["total"]

            cursor.execute(
                "SELECT COUNT(*) AS total FROM interviews WHERE employer_id=%s",
                (employer["id"],),
            )
            interviews = cursor.fetchone()["total"]

    return {
        "employer": employer,
        "counts": {
            "jobs": jobs,
            "applications": applications,
            "shortlists": shortlists,
            "interviews": interviews,
        },
    }


@router.get("/employer/candidate-search-v6", tags=["Employer Portal"])
def candidate_search_v6(
    search: str | None = Query(default=None, max_length=160),
    location: str | None = Query(default=None, max_length=160),
    skill: str | None = Query(default=None, max_length=160),
    qualification: str | None = Query(default=None, max_length=240),
    limit: int = Query(default=50, ge=1, le=100),
    _user=Depends(require_roles("employer", "admin")),
):
    conditions = ["p.visibility='employers'"]
    params: list = []

    if search:
        conditions.append(
            "(u.full_name ILIKE %s OR p.professional_title ILIKE %s)"
        )
        params.extend([f"%{search}%", f"%{search}%"])

    if location:
        conditions.append("p.location ILIKE %s")
        params.append(f"%{location}%")

    if skill:
        conditions.append(
            "EXISTS (SELECT 1 FROM skills s WHERE s.user_id=u.id AND s.name ILIKE %s)"
        )
        params.append(f"%{skill}%")

    if qualification:
        conditions.append(
            "EXISTS (SELECT 1 FROM education e WHERE e.user_id=u.id AND e.qualification ILIKE %s)"
        )
        params.append(f"%{qualification}%")

    params.append(limit)

    query = (
        "SELECT u.id,u.full_name,p.location,p.professional_title,"
        "p.professional_summary "
        "FROM users u "
        "JOIN profiles p ON p.user_id=u.id "
        f"WHERE {' AND '.join(conditions)} "
        "ORDER BY u.full_name "
        "LIMIT %s"
    )

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, tuple(params))
            return cursor.fetchall()


@router.post(
    "/ai-recruiter/job-match",
    response_model=JobMatchResponse,
    tags=["AI Recruiter"],
)
def ai_job_match(
    payload: JobMatchRequest,
    _user=Depends(get_current_user),
):
    return JobMatchResponse(
        **job_match(payload.cv_content, payload.job_description)
    )


@router.post("/career/cover-letter-v6", tags=["AI Career Assistant"])
def generate_cover_letter(
    payload: CoverLetterRequest,
    _user=Depends(get_current_user),
):
    return {
        "cover_letter": cover_letter(
            payload.candidate_name,
            payload.target_role,
            payload.company_name,
            payload.verified_strengths,
            payload.verified_experience,
        ),
        "warning": "Review and approve the letter. Only supplied facts were used.",
    }


@router.post("/career/interview-prep-v6", tags=["AI Career Assistant"])
def generate_interview_preparation(
    payload: InterviewPrepRequest,
    _user=Depends(get_current_user),
):
    return {
        "target_role": payload.target_role,
        "questions": interview_questions(
            payload.target_role,
            payload.job_description,
            payload.candidate_strengths,
        ),
    }


@router.post("/career/skills-gap-v6", tags=["AI Career Assistant"])
def generate_skills_gap(
    payload: SkillsGapRequest,
    _user=Depends(get_current_user),
):
    return skills_gap(
        payload.current_skills,
        payload.job_description,
    )


@router.post("/career/roadmap-v6", tags=["AI Career Assistant"])
def generate_career_roadmap(
    payload: CareerRoadmapRequest,
    _user=Depends(get_current_user),
):
    return career_roadmap(
        payload.current_role,
        payload.target_role,
        payload.qualifications,
        payload.skills,
    )
