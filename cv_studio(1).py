from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.repositories.cv_repository import CVRepository
from app.schemas.cv_draft import (
    CVDraftCreate,
    CVDraftResponse,
    CVDraftUpdate,
)
from app.services.cv_studio_service import CVStudioService

router = APIRouter(prefix="/api/cv-studio", tags=["CV Studio"])


def get_service(db: AsyncSession) -> CVStudioService:
    return CVStudioService(CVRepository(db))


@router.post("/drafts", response_model=CVDraftResponse, status_code=status.HTTP_201_CREATED)
async def create_draft(
    payload: CVDraftCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await get_service(db).create_draft(user.id, payload)


@router.get("/drafts", response_model=list[CVDraftResponse])
async def list_drafts(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await get_service(db).list_drafts(user.id)


@router.get("/drafts/{draft_id}", response_model=CVDraftResponse)
async def get_draft(
    draft_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await get_service(db).get_draft(user.id, draft_id)


@router.put("/drafts/{draft_id}", response_model=CVDraftResponse)
async def update_draft(
    draft_id: UUID,
    payload: CVDraftUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await get_service(db).update_draft(user.id, draft_id, payload)


@router.post("/drafts/{draft_id}/duplicate", response_model=CVDraftResponse)
async def duplicate_draft(
    draft_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await get_service(db).duplicate_draft(user.id, draft_id)


@router.delete("/drafts/{draft_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_draft(
    draft_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await get_service(db).delete_draft(user.id, draft_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
