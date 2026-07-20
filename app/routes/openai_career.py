"""Compatibility wrapper for the AI Career Engine router.

Older deployments import ``app.routes.openai_career``.  The maintained
implementation lives in :mod:`app.routes.ai_career_engine`.
"""

from app.routes.ai_career_engine import router

__all__ = ["router"]
