from __future__ import annotations

import os
from typing import Any

from fastapi import Header, HTTPException
from jose import JWTError, jwt


def current_user_id(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authentication required.")

    secret = os.getenv("JWT_SECRET_KEY") or os.getenv("JWT_SECRET")
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    if not secret:
        raise HTTPException(status_code=503, detail="JWT secret is not configured.")

    token = authorization.split(" ", 1)[1].strip()
    try:
        payload: dict[str, Any] = jwt.decode(token, secret, algorithms=[algorithm])
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token.") from exc

    for key in ("sub", "user_id", "id"):
        if payload.get(key) is not None:
            return str(payload[key])

    raise HTTPException(status_code=401, detail="Token does not contain a user identifier.")
