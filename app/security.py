from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
from pwdlib import PasswordHash

from app.config import settings


_password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using the recommended secure algorithm.
    """
    if not password:
        raise ValueError("Password cannot be empty.")

    return _password_hasher.hash(password)


def verify_password(
    password: str,
    hashed_password: str,
) -> bool:
    """
    Verify a plain-text password against a stored password hash.
    """
    if not password or not hashed_password:
        return False

    try:
        return _password_hasher.verify(
            password,
            hashed_password,
        )
    except Exception:
        return False


def create_token(
    user_id: str,
    role: str,
) -> str:
    """
    Create a signed access token for an authenticated user.
    """
    normalized_user_id = str(user_id).strip()
    normalized_role = str(role).strip().lower()

    if not normalized_user_id:
        raise ValueError("User ID is required.")

    if not normalized_role:
        raise ValueError("User role is required.")

    now = datetime.now(UTC)
    expires_at = now + timedelta(
        minutes=settings.access_token_minutes
    )

    payload = {
        "sub": normalized_user_id,
        "role": normalized_role,
        "type": "access",
        "iat": now,
        "nbf": now,
        "exp": expires_at,
        "jti": str(uuid4()),
        "iss": settings.app_name,
        "aud": settings.app_name,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> dict:
    """
    Decode and validate an access token.
    """
    if not token or not token.strip():
        raise jwt.InvalidTokenError("Token is required.")

    payload = jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
        issuer=settings.app_name,
        audience=settings.app_name,
        options={
            "require": [
                "sub",
                "role",
                "type",
                "iat",
                "nbf",
                "exp",
                "jti",
                "iss",
                "aud",
            ]
        },
    )

    if payload.get("type") != "access":
        raise jwt.InvalidTokenError(
            "Invalid token type."
        )

    if not payload.get("sub"):
        raise jwt.InvalidTokenError(
            "Token subject is missing."
        )

    if not payload.get("jti"):
        raise jwt.InvalidTokenError(
            "Token identifier is missing."
        )

    return payload
