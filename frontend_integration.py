from __future__ import annotations

from fastapi import APIRouter, Depends
from app.core.api_response import success_response
from app.core.monitoring import monitor_performance
from app.core.security import security_service
from app.services.subscription_access_service import (
    subscription_access_service,
    Feature,
    SubscriptionPlan,
)
from app.services.ai_professional_summary_service import AIProfessionalSummaryService

router = APIRouter(prefix="/studio", tags=["CV Studio"])


# Replace these placeholders with your existing authentication/user dependencies.
def get_current_user():
    return {
        "id": 1,
        "subscription_plan": SubscriptionPlan.PREMIUM,
        "ai_generations_today": 0,
    }


@router.post("/generate-summary")
@monitor_performance("generate_summary")
def generate_summary(
    payload: dict,
    current_user=Depends(get_current_user),
):
    security_service.require_authenticated_user(current_user)

    subscription_access_service.check_access(
        plan=current_user["subscription_plan"],
        feature=Feature.SUMMARY,
        generations_today=current_user["ai_generations_today"],
    )

    service = AIProfessionalSummaryService()

    result = service.generate(
        profile=payload.get("profile", {}),
        experience=payload.get("experience", []),
        target_role=payload.get("target_role"),
    )

    return success_response(
        data=result,
        message="Professional summary generated successfully.",
    )
