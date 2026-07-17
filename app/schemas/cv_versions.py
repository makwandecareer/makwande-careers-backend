from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class CVCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    target_role: str | None = Field(default=None, max_length=160)
    template_key: str = Field(default="real-01", max_length=120)
    content: dict[str, Any] = Field(default_factory=dict)


class CVUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    target_role: str | None = Field(default=None, max_length=160)
    template_key: str | None = Field(default=None, max_length=120)
    content: dict[str, Any] | None = None


class CVDuplicateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=160)


class CVResponse(BaseModel):
    id: str
    owner_id: str
    title: str
    target_role: str | None = None
    template_key: str
    content: dict[str, Any]
    version: int
    created_at: str
    updated_at: str


class CVVersionResponse(BaseModel):
    id: str
    cv_id: str
    owner_id: str
    version_number: int
    title: str
    target_role: str | None = None
    template_key: str
    content: dict[str, Any]
    created_at: str
