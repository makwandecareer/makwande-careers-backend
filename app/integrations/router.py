from __future__ import annotations

from fastapi import APIRouter

from app.config import settings

router = APIRouter(prefix="/integrations", tags=["Integrations"])


@router.get("/status")
def integration_status() -> dict:
    """Report whether server-side integration credentials are configured.

    Secret values are never returned.  This endpoint is safe for deployment
    diagnostics and does not make external API calls.
    """

    return settings.integration_status()
