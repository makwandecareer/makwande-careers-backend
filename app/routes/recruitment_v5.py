from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query

from app.database import get_connection
from app.dependencies import get_current_user, require_roles
from app.schemas_v5 import (
    AdminRoleUpdate,
    EmployerVerificationUpdate,
    InterviewCreate,
    InterviewUpdate,
    InvitationCreate,
    InvitationResponseUpdate,
    NotificationReadUpdate,
    SaveJobRequest,
)
from app.services.v5_helpers import (
    create_notification,
    get_employer_for_user,
    write_audit_log,
)

router = APIRouter(tags=["Recruitment Platform"])


@router.post("/candidate/saved-jobs", status_code=201, tags=["Candidate Dashboard"])
def save_job(payload: SaveJobRequest, user=Depends(get_current_user)):
    saved_id = str(uuid4())

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM jobs WHERE id=%s AND is_active=TRUE",
                (payload.job_id,),
            )
            if cursor.fetchone() is None:
                raise HTTPException(status_code=404, detail="Active job not found")

            try:
                cursor.execute(
                    '''
                    INSERT INTO saved_jobs (id,candidate_user_id,job_id)
                    VALUES (%s,%s,%s)
                    RETURNING *
                    ''',
                    (saved_id, user["id"], payload.job_id),
                )
                row = cursor.fetchone()
            except Exception as exc:
                raise HTTPException(status_code=409, detail="Job already saved") from exc
        connection.commit()

    return row


@router.get("/candidate/saved-jobs", tags=["Candidate Dashboard"])
def list_saved_jobs(user=Depends(get_current_user)):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                SELECT
                    s.*,
                    j.title,
                    j.location,
                    j.employment_type,
                    j.workplace_type,
                    e.company_name
                FROM saved_jobs s
                JOIN jobs j ON j.id=s.job_id
                JOIN employers e ON e.id=j.employer_id
                WHERE s.candidate_user_id=%s
                ORDER BY s.created_at DESC
                ''',
                (user["id"],),
            )
            return cursor.fetchall()


@router.delete("/candidate/saved-jobs/{saved_job_id}", status_code=204, tags=["Candidate Dashboard"])
def remove_saved_job(saved_job_id: str, user=Depends(get_current_user)):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                DELETE FROM saved_jobs
                WHERE id=%s AND candidate_user_id=%s
                RETURNING id
                ''',
                (saved_job_id, user["id"]),
            )
            deleted = cursor.fetchone()
        connection.commit()

    if deleted is None:
        raise HTTPException(status_code=404, detail="Saved job not found")


@router.get("/candidate/invitations", tags=["Candidate Dashboard"])
def candidate_invitations(user=Depends(get_current_user)):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                SELECT
                    i.*,
                    e.company_name,
                    j.title AS job_title
                FROM candidate_invitations i
                JOIN employers e ON e.id=i.employer_id
                LEFT JOIN jobs j ON j.id=i.job_id
                WHERE i.candidate_user_id=%s
                ORDER BY i.created_at DESC
                ''',
                (user["id"],),
            )
            return cursor.fetchall()


@router.put("/candidate/invitations/{invitation_id}", tags=["Candidate Dashboard"])
def respond_to_invitation(
    invitation_id: str,
    payload: InvitationResponseUpdate,
    user=Depends(get_current_user),
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                UPDATE candidate_invitations
                SET status=%s, updated_at=NOW()
                WHERE id=%s
                  AND candidate_user_id=%s
                  AND status='pending'
                RETURNING *
                ''',
                (payload.status, invitation_id, user["id"]),
            )
            row = cursor.fetchone()
        connection.commit()

    if row is None:
        raise HTTPException(status_code=404, detail="Pending invitation not found")

    write_audit_log(
        actor_user_id=str(user["id"]),
        action="candidate_invitation_response",
        entity_type="candidate_invitations",
        entity_id=invitation_id,
        metadata={"status": payload.status},
    )

    return row


@router.get("/candidate/interviews", tags=["Candidate Dashboard"])
def candidate_interviews(user=Depends(get_current_user)):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                SELECT
                    i.*,
                    e.company_name,
                    j.title AS job_title
                FROM interviews i
                JOIN employers e ON e.id=i.employer_id
                LEFT JOIN jobs j ON j.id=i.job_id
                WHERE i.candidate_user_id=%s
                ORDER BY i.scheduled_at
                ''',
                (user["id"],),
            )
            return cursor.fetchall()


@router.get("/candidate/notifications", tags=["Candidate Dashboard"])
def candidate_notifications(
    unread_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=100),
    user=Depends(get_current_user),
):
    query = "SELECT * FROM notifications WHERE user_id=%s"
    params: list = [user["id"]]

    if unread_only:
        query += " AND is_read=FALSE"

    query += " ORDER BY created_at DESC LIMIT %s"
    params.append(limit)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, tuple(params))
            return cursor.fetchall()


@router.put("/candidate/notifications/{notification_id}", tags=["Candidate Dashboard"])
def update_notification(
    notification_id: str,
    payload: NotificationReadUpdate,
    user=Depends(get_current_user),
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                UPDATE notifications
                SET is_read=%s
                WHERE id=%s AND user_id=%s
                RETURNING *
                ''',
                (payload.is_read, notification_id, user["id"]),
            )
            row = cursor.fetchone()
        connection.commit()

    if row is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return row


@router.post("/employer/invitations", status_code=201, tags=["Employer Portal"])
def invite_candidate(
    payload: InvitationCreate,
    user=Depends(require_roles("employer", "admin")),
):
    employer = get_employer_for_user(str(user["id"]))
    if employer is None:
        raise HTTPException(status_code=404, detail="Employer profile not found")

    invitation_id = str(uuid4())

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM users WHERE id=%s AND role='candidate'",
                (payload.candidate_user_id,),
            )
            if cursor.fetchone() is None:
                raise HTTPException(status_code=404, detail="Candidate not found")

            cursor.execute(
                '''
                INSERT INTO candidate_invitations (
                    id,employer_id,candidate_user_id,job_id,message
                )
                VALUES (%s,%s,%s,%s,%s)
                RETURNING *
                ''',
                (
                    invitation_id,
                    employer["id"],
                    payload.candidate_user_id,
                    payload.job_id,
                    payload.message,
                ),
            )
            row = cursor.fetchone()
        connection.commit()

    create_notification(
        user_id=payload.candidate_user_id,
        notification_type="employer_invitation",
        title=f"Invitation from {employer['company_name']}",
        message=payload.message or "An employer has invited you to discuss an opportunity.",
        action_url="/candidate/invitations",
    )

    write_audit_log(
        actor_user_id=str(user["id"]),
        action="candidate_invited",
        entity_type="candidate_invitations",
        entity_id=invitation_id,
        metadata={"candidate_user_id": payload.candidate_user_id},
    )

    return row


@router.get("/employer/invitations", tags=["Employer Portal"])
def employer_invitations(user=Depends(require_roles("employer", "admin"))):
    employer = get_employer_for_user(str(user["id"]))
    if employer is None:
        raise HTTPException(status_code=404, detail="Employer profile not found")

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                SELECT
                    i.*,
                    u.full_name,
                    u.email,
                    j.title AS job_title
                FROM candidate_invitations i
                JOIN users u ON u.id=i.candidate_user_id
                LEFT JOIN jobs j ON j.id=i.job_id
                WHERE i.employer_id=%s
                ORDER BY i.created_at DESC
                ''',
                (employer["id"],),
            )
            return cursor.fetchall()


@router.post("/employer/interviews", status_code=201, tags=["Employer Portal"])
def schedule_interview(
    payload: InterviewCreate,
    user=Depends(require_roles("employer", "admin")),
):
    employer = get_employer_for_user(str(user["id"]))
    if employer is None:
        raise HTTPException(status_code=404, detail="Employer profile not found")

    interview_id = str(uuid4())

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM users WHERE id=%s AND role='candidate'",
                (payload.candidate_user_id,),
            )
            if cursor.fetchone() is None:
                raise HTTPException(status_code=404, detail="Candidate not found")

            cursor.execute(
                '''
                INSERT INTO interviews (
                    id,application_id,employer_id,candidate_user_id,job_id,
                    scheduled_at,duration_minutes,meeting_url,location,notes
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING *
                ''',
                (
                    interview_id,
                    payload.application_id,
                    employer["id"],
                    payload.candidate_user_id,
                    payload.job_id,
                    payload.scheduled_at,
                    payload.duration_minutes,
                    payload.meeting_url,
                    payload.location,
                    payload.notes,
                ),
            )
            row = cursor.fetchone()
        connection.commit()

    create_notification(
        user_id=payload.candidate_user_id,
        notification_type="interview_scheduled",
        title=f"Interview scheduled by {employer['company_name']}",
        message=f"Your interview is scheduled for {payload.scheduled_at.isoformat()}.",
        action_url="/candidate/interviews",
    )

    write_audit_log(
        actor_user_id=str(user["id"]),
        action="interview_scheduled",
        entity_type="interviews",
        entity_id=interview_id,
        metadata={"candidate_user_id": payload.candidate_user_id},
    )

    return row


@router.get("/employer/interviews", tags=["Employer Portal"])
def employer_interviews(user=Depends(require_roles("employer", "admin"))):
    employer = get_employer_for_user(str(user["id"]))
    if employer is None:
        raise HTTPException(status_code=404, detail="Employer profile not found")

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                SELECT
                    i.*,
                    u.full_name,
                    u.email,
                    j.title AS job_title
                FROM interviews i
                JOIN users u ON u.id=i.candidate_user_id
                LEFT JOIN jobs j ON j.id=i.job_id
                WHERE i.employer_id=%s
                ORDER BY i.scheduled_at
                ''',
                (employer["id"],),
            )
            return cursor.fetchall()


@router.put("/employer/interviews/{interview_id}", tags=["Employer Portal"])
def update_interview(
    interview_id: str,
    payload: InterviewUpdate,
    user=Depends(require_roles("employer", "admin")),
):
    employer = get_employer_for_user(str(user["id"]))
    if employer is None:
        raise HTTPException(status_code=404, detail="Employer profile not found")

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=422, detail="No interview changes supplied")

    allowed = {
        "scheduled_at",
        "duration_minutes",
        "meeting_url",
        "location",
        "notes",
        "status",
    }

    assignments = []
    values = []

    for key, value in updates.items():
        if key in allowed:
            assignments.append(f"{key}=%s")
            values.append(value)

    assignments.append("updated_at=NOW()")
    values.extend([interview_id, employer["id"]])

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f'''
                UPDATE interviews
                SET {", ".join(assignments)}
                WHERE id=%s AND employer_id=%s
                RETURNING *
                ''',
                tuple(values),
            )
            row = cursor.fetchone()
        connection.commit()

    if row is None:
        raise HTTPException(status_code=404, detail="Interview not found")

    create_notification(
        user_id=str(row["candidate_user_id"]),
        notification_type="interview_updated",
        title="Interview updated",
        message="An employer updated your interview details.",
        action_url="/candidate/interviews",
    )

    return row


@router.get("/admin/overview", tags=["Administration"])
def admin_overview(_user=Depends(require_roles("admin"))):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total FROM users")
            users = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total FROM employers")
            employers = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total FROM jobs")
            jobs = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total FROM applications")
            applications = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total FROM interviews")
            interviews = cursor.fetchone()["total"]

    return {
        "users": users,
        "employers": employers,
        "jobs": jobs,
        "applications": applications,
        "interviews": interviews,
    }


@router.get("/admin/users", tags=["Administration"])
def admin_users(
    limit: int = Query(default=50, ge=1, le=200),
    _user=Depends(require_roles("admin")),
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                SELECT
                    id,email,full_name,role,is_active,created_at
                FROM users
                ORDER BY created_at DESC
                LIMIT %s
                ''',
                (limit,),
            )
            return cursor.fetchall()


@router.put("/admin/users/{user_id}/role", tags=["Administration"])
def admin_update_role(
    user_id: str,
    payload: AdminRoleUpdate,
    admin=Depends(require_roles("admin")),
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                UPDATE users
                SET role=%s
                WHERE id=%s
                RETURNING id,email,full_name,role,is_active,created_at
                ''',
                (payload.role, user_id),
            )
            row = cursor.fetchone()
        connection.commit()

    if row is None:
        raise HTTPException(status_code=404, detail="User not found")

    write_audit_log(
        actor_user_id=str(admin["id"]),
        action="user_role_updated",
        entity_type="users",
        entity_id=user_id,
        metadata={"role": payload.role},
    )

    return row


@router.put("/admin/employers/{employer_id}/verification", tags=["Administration"])
def admin_verify_employer(
    employer_id: str,
    payload: EmployerVerificationUpdate,
    admin=Depends(require_roles("admin")),
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                UPDATE employers
                SET verified=%s, updated_at=NOW()
                WHERE id=%s
                RETURNING *
                ''',
                (payload.verified, employer_id),
            )
            row = cursor.fetchone()
        connection.commit()

    if row is None:
        raise HTTPException(status_code=404, detail="Employer not found")

    write_audit_log(
        actor_user_id=str(admin["id"]),
        action="employer_verification_updated",
        entity_type="employers",
        entity_id=employer_id,
        metadata={"verified": payload.verified},
    )

    return row


@router.get("/admin/audit-logs", tags=["Administration"])
def admin_audit_logs(
    limit: int = Query(default=100, ge=1, le=500),
    _user=Depends(require_roles("admin")),
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                SELECT *
                FROM audit_logs
                ORDER BY created_at DESC
                LIMIT %s
                ''',
                (limit,),
            )
            return cursor.fetchall()
