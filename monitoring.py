from __future__ import annotations

import logging
import time
from functools import wraps
from typing import Callable, Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger("makwande.ai")


def log_ai_request(feature: str, user_id: int | None = None, **extra: Any) -> None:
    logger.info(
        "AI request",
        extra={
            "feature": feature,
            "user_id": user_id,
            **extra,
        },
    )


def log_ai_error(feature: str, error: Exception, user_id: int | None = None) -> None:
    logger.exception(
        "AI request failed",
        extra={
            "feature": feature,
            "user_id": user_id,
            "error": str(error),
        },
    )


def monitor_performance(feature: str):
    """
    Decorator to record execution time for AI operations.
    """

    def decorator(func: Callable[..., Any]):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed = round((time.perf_counter() - start) * 1000)
                logger.info(
                    "AI request completed",
                    extra={
                        "feature": feature,
                        "processing_time_ms": elapsed,
                    },
                )
                return result
            except Exception as exc:
                elapsed = round((time.perf_counter() - start) * 1000)
                logger.exception(
                    "AI request failed",
                    extra={
                        "feature": feature,
                        "processing_time_ms": elapsed,
                    },
                )
                raise

        return wrapper

    return decorator
