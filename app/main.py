from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.billing.routes import router as billing_router
from app.config import settings
from app.database import close_pool, init_database, open_pool
from app.database_account import init_account_database
from app.database_employer import init_employer_database
from app.database_employer_applications import (
    init_employer_application_database,
)
from app.database_features import init_feature_database
from app.integrations.router import router as integrations_router
from app.route_audit import collision_payload, find_route_collisions
from app.routes import (
    account,
    admin_analytics,
    ai_career_engine,
    ai_cv_v4_1,
    auth,
    candidate_applications,
    cv_versions,
    employer,
    employer_applications,
    platform,
    profile_source,
    recruitment_v5,
    structured,
    v6,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("makwande-careers")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Makwande Careers API")

    open_pool()

    init_database()
    init_feature_database()
    init_account_database()
    init_employer_database()
    init_employer_application_database()

    collisions = find_route_collisions(app)
    app.state.route_collisions = collisions

    if collisions:
        for collision in collisions:
            logger.warning(
                "Duplicate route registration detected: %s %s -> %s",
                collision.method,
                collision.path,
                ", ".join(collision.endpoint_names),
            )
    else:
        logger.info("No duplicate route registrations detected")

    logger.info("Makwande Careers API startup completed")

    try:
        yield
    finally:
        logger.info("Closing Makwande Careers database pool")
        close_pool()


app = FastAPI(
    title=settings.app_name,
    version="6.0.1",
    description="Makwande Careers full recruitment and AI platform",
    lifespan=lifespan,
    swagger_ui_parameters={
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "filter": True,
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Request-ID",
    ],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    request.state.request_id = request_id

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=()"
    )

    return response


# ----------------------------------------------------------------------
# System Endpoints
# ----------------------------------------------------------------------

@app.get(
    "/",
    tags=["System"],
    operation_id="system_root",
)
def root():
    return {
        "name": settings.app_name,
        "version": app.version,
        "status": "live",
        "docs": "/docs",
        "health": "/health",
    }


@app.get(
    "/health",
    tags=["System"],
    operation_id="system_health",
)
def health(request: Request):
    collisions = getattr(request.app.state, "route_collisions", [])

    return {
        "status": "ok",
        "service": settings.app_name,
        "version": app.version,
        "registered_routes": len(request.app.routes),
        "route_collision_count": len(collisions),
    }


@app.get(
    "/health/routes",
    tags=["System"],
    operation_id="system_route_health",
)
def route_health(request: Request):
    collisions = getattr(request.app.state, "route_collisions", [])

    return {
        "status": "attention" if collisions else "ok",
        "collision_count": len(collisions),
        "collisions": collision_payload(collisions),
    }


# ----------------------------------------------------------------------
# Existing Routers
# (Do NOT remove during Phase 1)
# ----------------------------------------------------------------------

app.include_router(auth.router, prefix="/api")
app.include_router(platform.router, prefix="/api")
app.include_router(structured.router, prefix="/api")
app.include_router(ai_career_engine.router, prefix="/api")
app.include_router(ai_cv_v4_1.router, prefix="/api")
app.include_router(recruitment_v5.router, prefix="/api")
app.include_router(v6.router, prefix="/api")
app.include_router(profile_source.router, prefix="/api")
app.include_router(cv_versions.router, prefix="/api")
app.include_router(integrations_router, prefix="/api")
app.include_router(billing_router, prefix="/api")
app.include_router(account.router, prefix="/api")
app.include_router(admin_analytics.router, prefix="/api")
app.include_router(employer.router, prefix="/api")
app.include_router(candidate_applications.router, prefix="/api")
app.include_router(employer_applications.router, prefix="/api")