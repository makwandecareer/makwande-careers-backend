from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cv import CVDraft


class CVRepository:
    """
    Production repository for CV Studio draft persistence.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, draft: CVDraft) -> CVDraft:
        self.db.add(draft)
        await self.db.commit()
        await self.db.refresh(draft)
        return draft

    async def get_by_id(self, draft_id: UUID) -> CVDraft | None:
        result = await self.db.execute(
            select(CVDraft).where(CVDraft.id == draft_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: UUID) -> Sequence[CVDraft]:
        result = await self.db.execute(
            select(CVDraft)
            .where(CVDraft.user_id == user_id)
            .order_by(CVDraft.updated_at.desc())
        )
        return result.scalars().all()

    async def update(self, draft: CVDraft) -> CVDraft:
        await self.db.commit()
        await self.db.refresh(draft)
        return draft

    async def delete(self, draft: CVDraft) -> None:
        await self.db.delete(draft)
        await self.db.commit()

    async def duplicate(self, draft: CVDraft) -> CVDraft:
        clone = CVDraft(
            user_id=draft.user_id,
            title=f"{draft.title} (Copy)",
            template_id=draft.template_id,
            profile=draft.profile,
            summary=draft.summary,
            experience=draft.experience,
            education=draft.education,
            skills=draft.skills,
            certifications=draft.certifications,
            projects=draft.projects,
            languages=draft.languages,
            references=draft.references,
            design=draft.design,
            metadata=draft.metadata,
        )
        return await self.create(clone)
