from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from psycopg import Error as PsycopgError

from app.database import get_connection
from app.security import decode_token


logger = logging.getLogger("makwande-careers.dependencies")

bearer_security = HTTPBearer(
    auto_error=False,
    scheme_name="BearerAuth",
    description="Enter a valid Makwande Careers access token.",
)


def authentication_error(
    detail: str = "Invalid or expired token",
) -> HTTPException:
    """Return a consistent authentication exception."""

    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def normalize_value(value: Any) -> str:
    """
    Convert enum values, strings and None into a normalized lowercase
    string for safe role and permission comparisons.
    """

    if value is None:
        return ""

    enum_value = getattr(value, "value", value)
    return str(enum_value).strip().lower()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_security
    ),
) -> dict[str, Any]:
    """
    Validate the bearer access token, confirm its server-side session,
    and return the active authenticated user.
    """

    if credentials is None:
        raise authentication_error("Authentication required")

    token = credentials.credentials.strip()

    if not token:
        raise authentication_error("Authentication required")

    try:
        payload = decode_token(token)

        if not isinstance(payload, dict):
            raise ValueError("Invalid token payload")

        user_id = payload.get("sub")
        token_jti = payload.get("jti")
        token_type = normalize_value(payload.get("type", "access"))

        if not user_id:
            raise ValueError("Token subject is missing")

        if not token_jti:
            raise ValueError("Token identifier is missing")

        if token_type != "access":
            raise ValueError("An access token is required")

    except (
        jwt.InvalidTokenError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        raise authentication_error() from exc

    try:
        with get_connection() as connection:
            try:
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
                              AND revoked_at IS NULL
                              AND expires_at > CURRENT_TIMESTAMP
                            """,
                            (
                                str(token_jti),
                                str(user_id),
                            ),
                        )

                connection.commit()

            except Exception:
                connection.rollback()
                raise

    except PsycopgError as exc:
        logger.exception(
            "Database failure while validating authenticated session"
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is temporarily unavailable",
        ) from exc

    if user is None:
        raise authentication_error(
            "Session is invalid, expired, or signed out"
        )

    authenticated_user = dict(user)

    if not bool(authenticated_user.get("is_active")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    authenticated_user["_token_payload"] = payload
    authenticated_user["_token_jti"] = str(token_jti)

    return authenticated_user


# Compatibility alias used by existing routes.
current_user = get_current_user


def require_roles(
    *allowed_roles: str,
) -> Callable[..., dict[str, Any]]:
    """
    Create a dependency that restricts an endpoint to one or more roles.
    """

    normalized_allowed_roles = {
        normalized_role
        for role in allowed_roles
        if (normalized_role := normalize_value(role))
    }

    if not normalized_allowed_roles:
        raise ValueError(
            "require_roles() must receive at least one valid role"
        )

    def role_checker(
        user: dict[str, Any] = Depends(get_current_user),
    ) -> dict[str, Any]:
        user_role = normalize_value(user.get("role"))

        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User role is missing",
            )

        if user_role not in normalized_allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return user

    return role_checker


# Compatibility alias used by existing routes.
roles = require_roles


def require_active_subscription(
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Allow access only when the authenticated user has an active and
    unexpired Makwande Careers subscription.
    """

    user_id = user.get("id")

    if not user_id:
        raise authentication_error(
            "Authenticated user ID is missing"
        )

    try:
        with get_connection() as connection:
            try:
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
                        (str(user_id),),
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
                        (str(user_id),),
                    )

                    subscription = cursor.fetchone()

                connection.commit()

            except Exception:
                connection.rollback()
                raise

    except PsycopgError as exc:
        logger.exception(
            "Database failure while validating subscription for user %s",
            user_id,
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Subscription service is temporarily unavailable",
        ) from exc

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
    Return True when the user has previously received a 14-day trial.
    """

    normalized_user_id = str(user_id).strip()

    if not normalized_user_id:
        return False

    try:
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
                    (normalized_user_id,),
                )

                result = cursor.fetchone()

    except PsycopgError as exc:
        logger.exception(
            "Database failure while checking trial usage for user %s",
            normalized_user_id,
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Subscription service is temporarily unavailable",
        ) from exc

    if result is None:
        return False

    if isinstance(result, dict):
        return bool(result.get("trial_used"))

    return bool(result[0])