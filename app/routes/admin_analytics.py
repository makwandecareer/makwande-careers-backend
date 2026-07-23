from __future__ import annotations

import os
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.database import get_connection
from app.dependencies import get_current_user

router = APIRouter(prefix="/admin/dashboard", tags=["Admin Analytics"])

Period = Literal["today", "7d", "30d", "90d", "12m"]

PERIOD_SQL: dict[str, str] = {
    "today": "date_trunc('day', CURRENT_TIMESTAMP)",
    "7d": "CURRENT_TIMESTAMP - INTERVAL '7 days'",
    "30d": "CURRENT_TIMESTAMP - INTERVAL '30 days'",
    "90d": "CURRENT_TIMESTAMP - INTERVAL '90 days'",
    "12m": "CURRENT_TIMESTAMP - INTERVAL '12 months'",
}


def serialize(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def serialize_rows(rows: list[Any]) -> list[dict[str, Any]]:
    return [
        {key: serialize(value) for key, value in dict(row).items()}
        for row in rows
    ]


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    configured_email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    user_email = str(user.get("email") or "").strip().lower()
    user_role = str(user.get("role") or "").strip().lower()

    if user_role == "admin" or (
        configured_email and user_email == configured_email
    ):
        return user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Administrator access is required.",
    )


@router.get("/analytics")
def executive_analytics(
    period: Period = Query("30d"),
    _admin: dict = Depends(require_admin),
) -> dict[str, Any]:
    start_expression = PERIOD_SQL[period]
    bucket = "month" if period == "12m" else "day"

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    (SELECT COUNT(*) FROM users) AS total_users,
                    (
                        SELECT COUNT(*)
                        FROM users
                        WHERE created_at >= {start_expression}
                    ) AS new_users,
                    (
                        SELECT COUNT(*)
                        FROM subscriptions
                        WHERE status::text = 'active'
                          AND starts_at <= CURRENT_TIMESTAMP
                          AND expires_at > CURRENT_TIMESTAMP
                    ) AS active_subscriptions,
                    (
                        SELECT COALESCE(SUM(expected_amount), 0)
                        FROM payment_transactions
                        WHERE status::text IN ('success', 'successful', 'paid')
                    ) AS total_revenue_cents,
                    (
                        SELECT COALESCE(SUM(expected_amount), 0)
                        FROM payment_transactions
                        WHERE status::text IN ('success', 'successful', 'paid')
                          AND COALESCE(paid_at, created_at) >= {start_expression}
                    ) AS period_revenue_cents,
                    (
                        SELECT COUNT(*)
                        FROM cvs
                        WHERE created_at >= {start_expression}
                    ) AS cvs_created,
                    (
                        SELECT COUNT(*)
                        FROM ats_assessments
                        WHERE created_at >= {start_expression}
                    ) AS ats_analyses,
                    (
                        (
                            SELECT COUNT(*)
                            FROM ai_revisions
                            WHERE created_at >= {start_expression}
                        ) +
                        (
                            SELECT COUNT(*)
                            FROM generated_cv_snapshots
                            WHERE created_at >= {start_expression}
                        )
                    ) AS ai_sessions
                """
            )
            metric_row = cursor.fetchone() or {}

            cursor.execute(
                f"""
                SELECT
                    COUNT(*) FILTER (
                        WHERE status::text IN ('success', 'successful', 'paid')
                    ) AS successful,
                    COUNT(*) FILTER (
                        WHERE status::text IN (
                            'failed', 'declined', 'cancelled', 'canceled'
                        )
                    ) AS failed,
                    COUNT(*) FILTER (
                        WHERE status::text NOT IN (
                            'success', 'successful', 'paid',
                            'failed', 'declined', 'cancelled', 'canceled'
                        )
                    ) AS pending
                FROM payment_transactions
                WHERE COALESCE(paid_at, created_at) >= {start_expression}
                """
            )
            payment_row = cursor.fetchone() or {}

            cursor.execute(
                f"""
                SELECT
                    date_trunc(
                        '{bucket}',
                        COALESCE(paid_at, created_at)
                    )::date AS date,
                    ROUND(
                        COALESCE(SUM(expected_amount), 0)::numeric / 100.0,
                        2
                    ) AS revenue,
                    COUNT(*) AS transactions
                FROM payment_transactions
                WHERE status::text IN ('success', 'successful', 'paid')
                  AND COALESCE(paid_at, created_at) >= {start_expression}
                GROUP BY 1
                ORDER BY 1
                """
            )
            revenue_trend = serialize_rows(cursor.fetchall())

            cursor.execute(
                f"""
                SELECT
                    date_trunc('{bucket}', created_at)::date AS date,
                    COUNT(*) AS registrations
                FROM users
                WHERE created_at >= {start_expression}
                GROUP BY 1
                ORDER BY 1
                """
            )
            user_growth = serialize_rows(cursor.fetchall())

            cursor.execute(
                """
                SELECT
                    plan_key::text AS plan,
                    COUNT(*) AS subscriptions
                FROM subscriptions
                WHERE status::text = 'active'
                  AND starts_at <= CURRENT_TIMESTAMP
                  AND expires_at > CURRENT_TIMESTAMP
                GROUP BY plan_key::text
                ORDER BY subscriptions DESC, plan
                """
            )
            subscription_breakdown = serialize_rows(cursor.fetchall())

            cursor.execute(
                """
                SELECT
                    pt.reference,
                    COALESCE(u.full_name, pt.email, 'Customer') AS customer,
                    COALESCE(u.email, pt.email) AS email,
                    ROUND(pt.expected_amount::numeric / 100.0, 2) AS amount,
                    pt.currency,
                    CASE
                        WHEN pt.status::text IN (
                            'success', 'successful', 'paid'
                        ) THEN 'success'
                        WHEN pt.status::text IN (
                            'failed', 'declined', 'cancelled', 'canceled'
                        ) THEN 'failed'
                        ELSE 'pending'
                    END AS status,
                    COALESCE(pt.paid_at, pt.created_at) AS date
                FROM payment_transactions pt
                LEFT JOIN users u ON u.id = pt.user_id
                ORDER BY COALESCE(pt.paid_at, pt.created_at) DESC
                LIMIT 10
                """
            )
            recent_payments = serialize_rows(cursor.fetchall())

            cursor.execute("SELECT 1 AS connected")
            database_connected = bool(
                (cursor.fetchone() or {}).get("connected")
            )

    return {
        "period": period,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "currency": "ZAR",
        "metrics": {
            "total_users": int(metric_row.get("total_users") or 0),
            "new_users": int(metric_row.get("new_users") or 0),
            "active_subscriptions": int(
                metric_row.get("active_subscriptions") or 0
            ),
            "total_revenue": (
                float(metric_row.get("total_revenue_cents") or 0) / 100
            ),
            "period_revenue": (
                float(metric_row.get("period_revenue_cents") or 0) / 100
            ),
            "cvs_created": int(metric_row.get("cvs_created") or 0),
            "ats_analyses": int(metric_row.get("ats_analyses") or 0),
            "ai_sessions": int(metric_row.get("ai_sessions") or 0),
        },
        "payment_status": {
            "successful": int(payment_row.get("successful") or 0),
            "pending": int(payment_row.get("pending") or 0),
            "failed": int(payment_row.get("failed") or 0),
        },
        "revenue_trend": revenue_trend,
        "user_growth": user_growth,
        "subscription_breakdown": subscription_breakdown,
        "recent_payments": recent_payments,
        "platform_health": {
            "status": "healthy" if database_connected else "degraded",
            "database": (
                "connected" if database_connected else "unavailable"
            ),
            "api": "operational",
        },
    }
