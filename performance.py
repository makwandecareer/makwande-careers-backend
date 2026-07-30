from fastapi import Request
from fastapi.responses import Response
from starlette.middleware.gzip import GZipMiddleware
import time

class PerformanceMiddleware:
    """
    Records request processing time and exposes it
    through the X-Process-Time header.
    """

    async def __call__(self, request: Request, call_next):
        start = time.perf_counter()
        response: Response = await call_next(request)
        elapsed = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{elapsed:.4f}"
        return response

def enable_gzip(app):
    app.add_middleware(GZipMiddleware, minimum_size=1024)
