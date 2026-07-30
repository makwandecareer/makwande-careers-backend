from __future__ import annotations

from datetime import datetime
from typing import Any


def success_response(
    data: Any,
    *,
    message: str = "Request completed successfully.",
    processing_time_ms: int | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "meta": meta or {},
    }
    if processing_time_ms is not None:
        payload["meta"]["processing_time_ms"] = processing_time_ms
    return payload


def error_response(
    *,
    message: str,
    error_code: str = "REQUEST_FAILED",
    details: Any = None,
    processing_time_ms: int | None = None,
) -> dict[str, Any]:
    payload = {
        "success": False,
        "message": message,
        "error": {
            "code": error_code,
            "details": details,
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "meta": {},
    }
    if processing_time_ms is not None:
        payload["meta"]["processing_time_ms"] = processing_time_ms
    return payload
