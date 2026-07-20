from fastapi import Header, HTTPException
from jose import jwt, JWTError
from app.core.integration_settings import settings

async def current_user_id(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Authentication required.")
    if not settings.jwt_secret_key:
        raise HTTPException(503, "JWT_SECRET_KEY is not configured.")
    try:
        payload = jwt.decode(authorization.split(" ",1)[1], settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise HTTPException(401, "Invalid or expired access token.") from exc
    for key in ("sub","user_id","id"):
        if payload.get(key) is not None:
            return str(payload[key])
    raise HTTPException(401, "Token has no user identifier.")
