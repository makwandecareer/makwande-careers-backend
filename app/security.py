from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import jwt
from pwdlib import PasswordHash

from app.config import settings


_password_hasher = PasswordHash.recommended()

_ALLOWED_JWT_ALGORITHMS = {
    "HS256",
    "HS384",
    "HS512",
}


def _validate_jwt_configuration() -> None:
    """
    Validate JWT settings before tokens are created or decoded.
    """

    jwt_secret = str(settings.jwt_secret or "").strip()
    jwt_algorithm = str(settings.jwt_algorithm or "").strip().upper()

    if len(jwt_secret) < 32:
        raise RuntimeError(
            "JWT secret must be configured and contain at least "
            "32 characters."
        )

    if jwt_algorithm not in _ALLOWED_JWT_ALGORITHMS:
        raise RuntimeError(
            "JWT algorithm must be one of: "
            f"{', '.join(sorted(_ALLOWED_JWT_ALGORITHMS))}."
        )

    if settings.access_token_minutes <= 0:
        raise RuntimeError(
            "Access token lifetime must be greater than zero minutes."
        )

    if not str(settings.app_name or "").strip():
        raise RuntimeError(
            "Application name must be configured for JWT issuer "
            "and audience validation."
        )


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using the recommended secure algorithm.
    """

    if not isinstance(password, str):
        raise TypeError("Password must be a string.")

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

    if not isinstance(password, str):
        return False

    if not isinstance(hashed_password, str):
        return False

    if not password or not hashed_password:
        return False

    try:
        return bool(
            _password_hasher.verify(
                password,
                hashed_password,
            )
        )
    except Exception:
        return False


def create_token(
    user_id: str,
    role: str,
) -> str:
    """
    Create a signed JWT access token for an authenticated user.
    """

    _validate_jwt_configuration()

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

    payload: dict[str, Any] = {
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

    token = jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )

    if isinstance(token, bytes):
        return token.decode("utf-8")

    return token


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a signed JWT access token.
    """

    _validate_jwt_configuration()

    if not isinstance(token, str):
        raise jwt.InvalidTokenError(
            "Token must be a string."
        )

    normalized_token = token.strip()

    if not normalized_token:
        raise jwt.InvalidTokenError(
            "Token is required."
        )

    payload = jwt.decode(
        normalized_token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
        issuer=settings.app_name,
        audience=settings.app_name,
        options={
            "verify_signature": True,
            "verify_exp": True,
            "verify_nbf": True,
            "verify_iat": True,
            "verify_aud": True,
            "verify_iss": True,
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
            ],
        },
    )

    if not isinstance(payload, dict):
        raise jwt.InvalidTokenError(
            "Invalid token payload."
        )

    token_type = str(
        payload.get("type") or ""
    ).strip().lower()

    if token_type != "access":
        raise jwt.InvalidTokenError(
            "Invalid token type."
        )

    subject = str(
        payload.get("sub") or ""
    ).strip()

    if not subject:
        raise jwt.InvalidTokenError(
            "Token subject is missing."
        )

    token_jti = str(
        payload.get("jti") or ""
    ).strip()

    if not token_jti:
        raise jwt.InvalidTokenError(
            "Token identifier is missing."
        )

    role = str(
        payload.get("role") or ""
    ).strip().lower()

    if not role:
        raise jwt.InvalidTokenError(
            "Token role is missing."
        )

    payload["sub"] = subject
    payload["jti"] = token_jti
    payload["role"] = role
    payload["type"] = token_type

    return payload


def is_access_token(
    payload: dict[str, Any],
) -> bool:
    """
    Return True when a decoded JWT payload represents an access token.
    """

    return (
        isinstance(payload, dict)
        and str(payload.get("type") or "").strip().lower()
        == "access"
    )