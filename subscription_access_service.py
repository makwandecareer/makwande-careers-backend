from __future__ import annotations

from enum import Enum
from fastapi import Depends, HTTPException, status

# Replace these imports with your project's implementations.
# from app.auth.dependencies import get_current_user
# from app.models.user import User


class SubscriptionPlan(str, Enum):
    TRIAL = "trial"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class Feature(str, Enum):
    CV_ANALYSIS = "cv_analysis"
    SUMMARY = "summary"
    ACHIEVEMENTS = "achievements"
    JOB_MATCH = "job_match"
    COVER_LETTER = "cover_letter"
    INTERVIEW = "interview"
    CAREER_COACH = "career_coach"


FEATURE_LIMITS = {
    SubscriptionPlan.TRIAL: {
        "daily_generations": 10,
    },
    SubscriptionPlan.PREMIUM: {
        "daily_generations": 500,
    },
    SubscriptionPlan.ENTERPRISE: {
        "daily_generations": -1,  # unlimited
    },
}


class SubscriptionAccessService:
    """
    Central subscription and feature access validator.
    """

    def check_access(
        self,
        *,
        plan: SubscriptionPlan,
        feature: Feature,
        generations_today: int,
    ) -> None:
        limits = FEATURE_LIMITS[plan]
        limit = limits["daily_generations"]

        if limit != -1 and generations_today >= limit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Daily AI generation limit reached for your subscription. "
                    "Upgrade your plan or try again tomorrow."
                ),
            )

        # Future extension:
        # - Per-feature permissions
        # - Billing status validation
        # - Subscription expiry
        # - Team/organization quotas
        # - Promotional credits


subscription_access_service = SubscriptionAccessService()
