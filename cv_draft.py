from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DesignSettings(BaseModel):
    primary_color: str = "#0F766E"
    secondary_color: str = "#E6FFFA"
    font_family: str = "Inter"
    spacing: str = "normal"
    layout: str = "modern"


class CVDraftCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    template_id: str = "modern"


class CVDraftUpdate(BaseModel):
    title: str | None = None
    template_id: str | None = None
    profile: dict[str, Any] | None = None
    summary: str | None = None
    experience: list[dict[str, Any]] | None = None
    education: list[dict[str, Any]] | None = None
    skills: list[dict[str, Any]] | None = None
    certifications: list[dict[str, Any]] | None = None
    projects: list[dict[str, Any]] | None = None
    languages: list[dict[str, Any]] | None = None
    references: list[dict[str, Any]] | None = None
    design: DesignSettings | None = None


class CVDraftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    template_id: str
    version: int
    profile: dict[str, Any]
    summary: str | None
    experience: list[dict[str, Any]]
    education: list[dict[str, Any]]
    skills: list[dict[str, Any]]
    certifications: list[dict[str, Any]]
    projects: list[dict[str, Any]]
    languages: list[dict[str, Any]]
    references: list[dict[str, Any]]
    design: dict[str, Any]
    created_at: datetime
    updated_at: datetime
