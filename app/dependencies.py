import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.database import get_connection
from app.security import decode_token


bearer_security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_security),
) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.database import get_connection
from app.security import decode_token


bearer_security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_security
    ),
) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    try:
        payload = decode_token(credentials.credentials)
        user_id = payload["sub"]

    except (jwt.InvalidTokenError, KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM users
                WHERE id = %s
                """,
                (user_id,),
            )
            user = cursor.fetchone()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found",
        )

    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    return user


# Compatibility name used by platform.py
current_user = get_current_user


def require_roles(*allowed_roles: str):
    def role_checker(
        user: dict = Depends(get_current_user),
    ) -> dict:
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return user

    return role_checker


# Compatibility name used by platform.py
roles = require_roles


def require_active_subscription(
    user: dict = Depends(get_current_user),
) -> dict:
    """
    Allows access only when the logged-in user has an active,
    unexpired subscription.
    """

    user_id = str(user["id"])

    with get_connection() as connection:
        with connection.cursor() as cursor:
            # Automatically expire subscriptions whose time has ended.
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
                    id,
                    plan_code,
                    amount,
                    currency,
                    status,
                    starts_at,
                    expires_at
                FROM subscriptions
                WHERE user_id = %s
                  AND status = 'active'
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
    Returns True when the user has previously received the
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
                      AND plan_code IN (
                          'trial_14_day',
                          'trial_14_days'
                      )
                ) AS trial_used
                """,
                (user_id,),
            )

            result = cursor.fetchone()

    return bool(result and result["trial_used"])