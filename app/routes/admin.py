from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.database import get_connection
from app.dependencies import get_current_user

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


def serialize(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Allow database admins or the email configured in ADMIN_EMAIL."""
    configured_email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    user_email = str(user.get("email") or "").strip().lower()
    user_role = str(user.get("role") or "").strip().lower()

    if user_role == "admin":
        return user

    if configured_email and user_email == configured_email:
        return user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Administrator access is required.",
    )


class AdminUserUpdate(BaseModel):
    status: Literal["active", "suspended"] | None = None
    role: Literal["candidate", "employer", "admin"] | None = None


def dashboard_metrics(cursor) -> dict[str, Any]:
    cursor.execute(
        """
        SELECT
            (SELECT COUNT(*) FROM users) AS total_users,
            (
                SELECT COUNT(*)
                FROM subscriptions
                WHERE status = 'active'
                  AND starts_at <= CURRENT_TIMESTAMP
                  AND expires_at > CURRENT_TIMESTAMP
            ) AS active_subscriptions,
            (
                SELECT COALESCE(SUM(expected_amount), 0)
                FROM payment_transactions
                WHERE status IN ('success', 'successful', 'paid')
                  AND COALESCE(paid_at, created_at) >= date_trunc('month', CURRENT_TIMESTAMP)
            ) AS monthly_revenue_cents,
            (SELECT COUNT(*) FROM cvs) AS cvs_created,
            (SELECT COUNT(*) FROM ats_assessments) AS ats_analyses,
            (
                (SELECT COUNT(*) FROM ai_revisions) +
                (SELECT COUNT(*) FROM generated_cv_snapshots)
            ) AS ai_sessions
        """
    )
    row = cursor.fetchone() or {}
    return {
        "total_users": int(row.get("total_users") or 0),
        "active_subscriptions": int(row.get("active_subscriptions") or 0),
        "monthly_revenue": float(row.get("monthly_revenue_cents") or 0) / 100,
        "cvs_created": int(row.get("cvs_created") or 0),
        "ats_analyses": int(row.get("ats_analyses") or 0),
        "ai_sessions": int(row.get("ai_sessions") or 0),
    }


@router.get("/dashboard")
def admin_dashboard(_admin: dict = Depends(require_admin)) -> dict[str, Any]:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            metrics = dashboard_metrics(cursor)

    return {"metrics": metrics}


@router.get("/overview")
def admin_overview(_admin: dict = Depends(require_admin)) -> dict[str, Any]:
    return admin_dashboard(_admin)


@router.get("/users")
def admin_users(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    _admin: dict = Depends(require_admin),
) -> dict[str, Any]:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    u.id,
                    u.full_name AS name,
                    u.email,
                    u.role,
                    CASE WHEN u.is_active THEN 'active' ELSE 'suspended' END AS status,
                    COALESCE(active_subscription.plan_key, 'Free') AS plan,
                    u.created_at AS joined_at,
                    latest_session.last_seen_at AS last_active
                FROM users u
                LEFT JOIN LATERAL (
                    SELECT s.plan_key
                    FROM subscriptions s
                    WHERE s.user_id = u.id
                      AND s.status = 'active'
                      AND s.starts_at <= CURRENT_TIMESTAMP
                      AND s.expires_at > CURRENT_TIMESTAMP
                    ORDER BY s.expires_at DESC
                    LIMIT 1
                ) active_subscription ON TRUE
                LEFT JOIN LATERAL (
                    SELECT us.last_seen_at
                    FROM user_sessions us
                    WHERE us.user_id = u.id
                    ORDER BY us.last_seen_at DESC
                    LIMIT 1
                ) latest_session ON TRUE
                ORDER BY u.created_at DESC
                LIMIT %s OFFSET %s
                """,
                (limit, offset),
            )
            rows = cursor.fetchall()

    users = [
        {key: serialize(value) for key, value in dict(row).items()}
        for row in rows
    ]
    return {"users": users, "limit": limit, "offset": offset}


@router.patch("/users/{user_id}")
def update_admin_user(
    user_id: str,
    payload: AdminUserUpdate,
    admin: dict = Depends(require_admin),
) -> dict[str, Any]:
    if str(admin.get("id")) == user_id and payload.status == "suspended":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot suspend your own administrator account.",
        )

    assignments: list[str] = []
    values: list[Any] = []

    if payload.status is not None:
        assignments.append("is_active = %s")
        values.append(payload.status == "active")

    if payload.role is not None:
        assignments.append("role = %s")
        values.append(payload.role)

    if not assignments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No user changes were supplied.",
        )

    values.append(user_id)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                UPDATE users
                SET {', '.join(assignments)}
                WHERE id = %s
                RETURNING id, full_name AS name, email, role,
                          CASE WHEN is_active THEN 'active' ELSE 'suspended' END AS status,
                          created_at AS joined_at
                """,
                tuple(values),
            )
            updated = cursor.fetchone()

        connection.commit()

    if updated is None:
        raise HTTPException(status_code=404, detail="User not found.")

    return {key: serialize(value) for key, value in dict(updated).items()}


@router.get("/payments")
def admin_payments(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    _admin: dict = Depends(require_admin),
) -> dict[str, Any]:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    pt.reference AS id,
                    COALESCE(u.full_name, pt.email, 'Customer') AS user_name,
                    COALESCE(u.email, pt.email) AS email,
                    (pt.expected_amount::numeric / 100.0) AS amount,
                    pt.currency,
                    CASE
                        WHEN pt.status IN ('success', 'successful', 'paid') THEN 'success'
                        WHEN pt.status IN ('failed', 'declined', 'cancelled', 'canceled') THEN 'failed'
                        ELSE 'pending'
                    END AS status,
                    pt.reference,
                    COALESCE(pt.paid_at, pt.created_at) AS paid_at
                FROM payment_transactions pt
                LEFT JOIN users u ON u.id = pt.user_id
                ORDER BY COALESCE(pt.paid_at, pt.created_at) DESC
                LIMIT %s OFFSET %s
                """,
                (limit, offset),
            )
            rows = cursor.fetchall()

    payments = [
        {key: serialize(value) for key, value in dict(row).items()}
        for row in rows
    ]
    return {"payments": payments, "limit": limit, "offset": offset}


@router.get("/transactions")
def admin_transactions(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    admin: dict = Depends(require_admin),
) -> dict[str, Any]:
    return admin_payments(limit=limit, offset=offset, _admin=admin)


@router.get("/activity")
def admin_activity(
    limit: int = Query(100, ge=1, le=300),
    _admin: dict = Depends(require_admin),
) -> dict[str, Any]:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM (
                    SELECT
                        'user-' || u.id::text AS id,
                        'New user registered' AS title,
                        u.full_name || ' joined Makwande Careers.' AS description,
                        u.created_at AS created_at,
                        'user' AS type
                    FROM users u

                    UNION ALL

                    SELECT
                        'payment-' || pt.reference AS id,
                        CASE
                            WHEN pt.status IN ('success', 'successful', 'paid')
                                THEN 'Payment completed'
                            WHEN pt.status IN ('failed', 'declined', 'cancelled', 'canceled')
                                THEN 'Payment failed'
                            ELSE 'Payment initiated'
                        END AS title,
                        COALESCE(u.full_name, pt.email, 'A customer') ||
                        ' — ' || pt.reference AS description,
                        COALESCE(pt.paid_at, pt.created_at) AS created_at,
                        'payment' AS type
                    FROM payment_transactions pt
                    LEFT JOIN users u ON u.id = pt.user_id

                    UNION ALL

                    SELECT
                        'cv-' || c.id::text AS id,
                        'CV created' AS title,
                        COALESCE(u.full_name, 'A user') || ' created “' || c.title || '”.' AS description,
                        c.created_at AS created_at,
                        'cv' AS type
                    FROM cvs c
                    LEFT JOIN users u ON u.id = c.owner_id

                    UNION ALL

                    SELECT
                        'security-' || se.id::text AS id,
                        'Security event' AS title,
                        COALESCE(u.full_name, 'A user') || ' — ' || se.event_type AS description,
                        se.created_at AS created_at,
                        'security' AS type
                    FROM security_events se
                    LEFT JOIN users u ON u.id = se.user_id
                ) activity
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cursor.fetchall()

    activities = [
        {key: serialize(value) for key, value in dict(row).items()}
        for row in rows
    ]
    return {"activities": activities}


@router.get("/audit-logs")
def admin_audit_logs(
    limit: int = Query(100, ge=1, le=300),
    admin: dict = Depends(require_admin),
) -> dict[str, Any]:
    return admin_activity(limit=limit, _admin=admin)
