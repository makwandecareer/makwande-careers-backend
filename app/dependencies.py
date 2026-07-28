from __future__ import annotations

from typing import Any, Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.database import get_connection
from app.security import decode_token


bearer_security = HTTPBearer(auto_error=False)


def normalize_value(value: Any) -> str:
    """
    Convert database enum values, strings and None into a normalized
    lowercase string for safe role and permission comparisons.
    """
    if value is None:
        return ""

    enum_value = getattr(value, "value", value)
    return str(enum_value).strip().lower()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_security
    ),
) -> dict:
    """
    Validate the access token, verify its server-side session and return
    the active authenticated user.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(credentials.credentials)

        user_id = payload.get("sub")
        token_jti = payload.get("jti")

        if not user_id or not token_jti:
            raise ValueError("Token is missing required claims")

    except (
        jwt.InvalidTokenError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT u.*
                FROM users AS u
                INNER JOIN user_sessions AS s
                    ON s.user_id = u.id
                WHERE u.id = %s
                  AND s.token_jti = %s
                  AND s.revoked_at IS NULL
                  AND s.expires_at > CURRENT_TIMESTAMP
                LIMIT 1
                """,
                (
                    str(user_id),
                    str(token_jti),
                ),
            )

            user = cursor.fetchone()

            if user is not None:
                cursor.execute(
                    """
                    UPDATE user_sessions
                    SET last_seen_at = CURRENT_TIMESTAMP
                    WHERE token_jti = %s
                      AND user_id = %s
                    """,
                    (
                        str(token_jti),
                        str(user_id),
                    ),
                )

        connection.commit()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session is invalid, expired, or signed out",
            headers={"WWW-Authenticate": "Bearer"},
        )

    authenticated_user = dict(user)

    if not bool(authenticated_user.get("is_active")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    authenticated_user["_token_payload"] = payload

    return authenticated_user


# Compatibility name used by existing routes.
current_user = get_current_user


def require_roles(
    *allowed_roles: str,
) -> Callable[..., dict]:
    """
    Create a FastAPI dependency that restricts an endpoint to one or
    more allowed user roles.
    """
    normalized_allowed_roles = {
        normalize_value(role)
        for role in allowed_roles
        if normalize_value(role)
    }

    if not normalized_allowed_roles:
        raise ValueError(
            "require_roles() must receive at least one valid role"
        )

    def role_checker(
        user: dict = Depends(get_current_user),
    ) -> dict:
        user_role = normalize_value(user.get("role"))
        user_email = normalize_value(user.get("email"))
        configured_admin_email = normalize_value(settings.admin_email)

        role_is_allowed = user_role in normalized_allowed_roles

        email_is_configured_admin = (
            "admin" in normalized_allowed_roles
            and bool(configured_admin_email)
            and user_email == configured_admin_email
        )

        if not role_is_allowed and not email_is_configured_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return user

    return role_checker


# Compatibility name used by existing routes.
roles = require_roles


def require_active_subscription(
    user: dict = Depends(get_current_user),
) -> dict:
    """
    Allow access only when the authenticated user has an active,
    unexpired Makwande Careers subscription.
    """
    user_id = str(user["id"])

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE subscriptions
                SET
                    status = 'expired',
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
                  AND status = 'active'
                  AND expires_at <= CURRENT_TIMESTAMP
                """,
                (user_id,),
            )

            cursor.execute(
                """
                SELECT
                    user_id,
                    plan_key,
                    status,
                    starts_at,
                    expires_at,
                    payment_reference,
                    updated_at
                FROM subscriptions
                WHERE user_id = %s
                  AND status = 'active'
                  AND starts_at <= CURRENT_TIMESTAMP
                  AND expires_at > CURRENT_TIMESTAMP
                ORDER BY expires_at DESC
                LIMIT 1
                """,
                (user_id,),
            )

            subscription = cursor.fetchone()

        connection.commit()

    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "SUBSCRIPTION_REQUIRED",
                "message": (
                    "An active Makwande Careers subscription "
                    "is required to use this feature."
                ),
                "redirect_to": "/dashboard/billing",
            },
        )

    authenticated_user = dict(user)
    authenticated_user["subscription"] = dict(subscription)

    return authenticated_user


def has_used_trial(user_id: str) -> bool:
    """
    Return True when the user has previously received the
    14-day introductory trial.
    """
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM subscriptions
                    WHERE user_id = %s
                      AND plan_key IN (
                          'trial_14_day',
                          'trial_14_days'
                      )
                ) AS trial_used
                """,
                (str(user_id),),
            )

            result = cursor.fetchone()

    if result is None:
        return False

    if isinstance(result, dict):
        return bool(result.get("trial_used"))

    return bool(result[0])