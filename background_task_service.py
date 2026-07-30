from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable, Any


class BackgroundTaskService:
    """
    Simple background task manager.

    Replace with Celery, RQ, or Dramatiq in production for
    distributed processing and retries.
    """

    def __init__(self, max_workers: int = 4):
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    def submit(self, func: Callable[..., Any], *args, **kwargs) -> Future:
        """Run a task asynchronously."""
        return self._executor.submit(func, *args, **kwargs)

    def shutdown(self) -> None:
        self._executor.shutdown(wait=True)


background_tasks = BackgroundTaskService()


# Example wrappers

def generate_pdf(export_service, payload):
    return export_service.build_pdf(payload)


def generate_docx(export_service, payload):
    return export_service.build_docx(payload)


def analyze_cv(ai_service, draft):
    return ai_service.analyse(draft)


def generate_cover_letter(ai_service, profile, company, role, description=""):
    return ai_service.generate(
        profile=profile,
        company_name=company,
        job_title=role,
        job_description=description,
    )
