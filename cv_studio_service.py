from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status

from app.models.cv import CVDraft
from app.repositories.cv_repository import CVRepository
from app.schemas.cv_draft import CVDraftCreate, CVDraftUpdate


class CVStudioService:
    """
    Production business logic for CV Studio.
    """

    def __init__(self, repository: CVRepository):
        self.repository = repository

    async def create_draft(self, user_id: UUID, payload: CVDraftCreate) -> CVDraft:
        draft = CVDraft(
            user_id=user_id,
            title=payload.title,
            template_id=payload.template_id,
        )
        return await self.repository.create(draft)

    async def get_draft(self, user_id: UUID, draft_id: UUID) -> CVDraft:
        draft = await self.repository.get_by_id(draft_id)
        self._assert_owner(draft, user_id)
        return draft

    async def list_drafts(self, user_id: UUID):
        return await self.repository.list_by_user(user_id)

    async def update_draft(
        self,
        user_id: UUID,
        draft_id: UUID,
        payload: CVDraftUpdate,
    ) -> CVDraft:
        draft = await self.repository.get_by_id(draft_id)
        self._assert_owner(draft, user_id)

        updates = payload.model_dump(exclude_unset=True)
        for key, value in updates.items():
            setattr(draft, key, value)

        draft.version += 1
        return await self.repository.update(draft)

    async def duplicate_draft(self, user_id: UUID, draft_id: UUID) -> CVDraft:
        draft = await self.repository.get_by_id(draft_id)
        self._assert_owner(draft, user_id)
        return await self.repository.duplicate(draft)

    async def delete_draft(self, user_id: UUID, draft_id: UUID) -> None:
        draft = await self.repository.get_by_id(draft_id)
        self._assert_owner(draft, user_id)
        await self.repository.delete(draft)

    @staticmethod
    def _assert_owner(draft: CVDraft | None, user_id: UUID) -> None:
        if draft is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CV draft not found.",
            )
        if draft.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this CV draft.",
            )
