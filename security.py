from __future__ import annotations

from fastapi import HTTPException, Request, status
from collections import defaultdict
import time


class SecurityService:
    """
    Production security helpers.
    Integrate JWT authentication with your existing auth module.
    """

    def __init__(self) -> None:
        self._requests = defaultdict(list)

    def validate_payload_size(
        self,
        request: Request,
        *,
        max_bytes: int = 2 * 1024 * 1024,
    ) -> None:
        length = request.headers.get("content-length")
        if length and int(length) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Request payload exceeds the allowed size.",
            )

    def rate_limit(
        self,
        identifier: str,
        *,
        limit: int = 60,
        window_seconds: int = 60,
    ) -> None:
        now = time.time()
        entries = [t for t in self._requests[identifier] if now - t < window_seconds]
        if len(entries) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
            )
        entries.append(now)
        self._requests[identifier] = entries

    def require_authenticated_user(self, user) -> None:
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required.",
            )

security_service = SecurityService()
