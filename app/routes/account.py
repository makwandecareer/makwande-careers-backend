from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.database import get_connection
from app.dependencies import get_current_user
from app.security import hash_password, verify_password


router = APIRouter(prefix="/account", tags=["Account"])


class AccountSettingsUpdate(BaseModel):
    theme: str = Field(default="system", pattern="^(light|dark|system)$")
    language: str = Field(default="en", max_length=10)
    timezone: str = Field(default="Africa/Johannesburg", max_length=80)
    ai_personalisation: bool = True
    profile_discoverable: bool = False
    product_updates: bool = True
    job_alerts: bool = True
    application_updates: bool = True
    interview_reminders: bool = True
    security_alerts: bool = True
    email_notifications: bool = True


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=12, max_length=128)


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()[:80]
    return request.client.host[:80] if request.client else None


@router.get("/settings")
def get_settings(user=Depends(get_current_user)):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO account_preferences(user_id) VALUES(%s)
                ON CONFLICT(user_id) DO NOTHING
                """,
                (user["id"],),
            )
            cursor.execute(
                "SELECT * FROM account_preferences WHERE user_id=%s",
                (user["id"],),
            )
            preferences = cursor.fetchone()
        connection.commit()
    return preferences


@router.put("/settings")
def update_settings(payload: AccountSettingsUpdate, user=Depends(get_current_user)):
    values = payload.model_dump()
    columns = list(values)
    assignments = ", ".join(f"{column}=EXCLUDED.{column}" for column in columns)
    placeholders = ", ".join(["%s"] * (len(columns) + 1))
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO account_preferences(user_id, {', '.join(columns)})
                VALUES({placeholders})
                ON CONFLICT(user_id) DO UPDATE SET
                    {assignments}, updated_at=NOW()
                RETURNING *
                """,
                (user["id"], *values.values()),
            )
            row = cursor.fetchone()
        connection.commit()
    return row


@router.get("/security/sessions")
def list_sessions(user=Depends(get_current_user)):
    current_jti = str(user["_token_payload"]["jti"])
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, user_agent, ip_address, created_at, last_seen_at,
                       expires_at, token_jti::text=%s AS is_current
                FROM user_sessions
                WHERE user_id=%s AND revoked_at IS NULL AND expires_at>NOW()
                ORDER BY last_seen_at DESC
                """,
                (current_jti, user["id"]),
            )
            return cursor.fetchall()


@router.delete("/security/sessions/{session_id}", status_code=204)
def revoke_session(session_id: str, user=Depends(get_current_user)):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE user_sessions SET revoked_at=NOW()
                WHERE id=%s AND user_id=%s AND revoked_at IS NULL
                RETURNING id
                """,
                (session_id, user["id"]),
            )
            row = cursor.fetchone()
        connection.commit()
    if row is None:
        raise HTTPException(status_code=404, detail="Active session not found")


@router.post("/security/sign-out-others")
def sign_out_others(user=Depends(get_current_user)):
    current_jti = str(user["_token_payload"]["jti"])
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE user_sessions SET revoked_at=NOW()
                WHERE user_id=%s AND token_jti::text<>%s AND revoked_at IS NULL
                """,
                (user["id"], current_jti),
            )
            count = cursor.rowcount
        connection.commit()
    return {"revoked_sessions": count}


@router.post("/security/change-password")
def change_password(
    payload: PasswordChangeRequest,
    request: Request,
    user=Depends(get_current_user),
):
    if not verify_password(payload.current_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if verify_password(payload.new_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Choose a different password")

    current_jti = str(user["_token_payload"]["jti"])
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET password_hash=%s WHERE id=%s",
                (hash_password(payload.new_password), user["id"]),
            )
            cursor.execute(
                """
                UPDATE user_sessions SET revoked_at=NOW()
                WHERE user_id=%s AND token_jti::text<>%s AND revoked_at IS NULL
                """,
                (user["id"], current_jti),
            )
            cursor.execute(
                """
                INSERT INTO security_events(
                    id, user_id, event_type, ip_address, user_agent
                ) VALUES(%s,%s,'password_changed',%s,%s)
                """,
                (
                    str(uuid4()),
                    user["id"],
                    _client_ip(request),
                    request.headers.get("user-agent", "")[:1000],
                ),
            )
        connection.commit()
    return {"message": "Password updated and other sessions signed out"}


@router.get("/security/activity")
def security_activity(user=Depends(get_current_user)):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, event_type, ip_address, user_agent, created_at
                FROM security_events WHERE user_id=%s
                ORDER BY created_at DESC LIMIT 50
                """,
                (user["id"],),
            )
            return cursor.fetchall()


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(user=Depends(get_current_user)):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE user_sessions SET revoked_at=NOW() WHERE token_jti=%s",
                (user["_token_payload"]["jti"],),
            )
        connection.commit()
