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

    try:
        payload = decode_token(credentials.credentials)
        user_id = payload["sub"]

    except (jwt.InvalidTokenError, KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        ) from exc

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM users WHERE id = %s",
                (user_id,),
            )
            user = cursor.fetchone()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User account not found",
        )

    if not user["is_active"]:
        raise HTTPException(
            status_code=403,
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
                status_code=403,
                detail="Insufficient permissions",
            )

        return user

    return role_checker


# Compatibility name used by platform.py
roles = require_roles