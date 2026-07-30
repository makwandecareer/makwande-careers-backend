from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["Admin Portal"])


@router.get("/dashboard")
def admin_dashboard():
    """
    Placeholder admin dashboard.
    Replace with live database metrics and RBAC authorization.
    """
    return {
        "users": {
            "total": 15234,
            "active": 12011,
            "new_today": 43,
        },
        "employers": {
            "registered": 286,
            "verified": 241,
        },
        "subscriptions": {
            "trial": 812,
            "premium": 436,
            "expired": 97,
        },
        "platform": {
            "jobs": 1254,
            "applications": 48126,
            "cv_exports": 30587,
            "ai_requests_today": 5291,
        },
        "health": {
            "api": "healthy",
            "database": "healthy",
            "queue": "healthy",
            "storage": "healthy",
        },
    }


@router.get("/audit-log")
def audit_log():
    return {
        "events": [],
        "message": "Connect to persistent audit logging."
    }


@router.get("/system-status")
def system_status():
    return {
        "version": "1.0.0",
        "environment": "production",
        "uptime": "99.9%",
    }
