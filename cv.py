from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class CVDraft(Base):
    """
    Production CV Studio Draft model.
    """

    __tablename__ = "cv_drafts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title = Column(String(255), nullable=False, default="Untitled CV")
    template_id = Column(String(100), nullable=False, default="modern")
    version = Column(Integer, nullable=False, default=1)
    is_default = Column(Boolean, nullable=False, default=False)

    profile = Column(JSON, nullable=False, default=dict)
    summary = Column(Text, nullable=True)
    experience = Column(JSON, nullable=False, default=list)
    education = Column(JSON, nullable=False, default=list)
    skills = Column(JSON, nullable=False, default=list)
    certifications = Column(JSON, nullable=False, default=list)
    projects = Column(JSON, nullable=False, default=list)
    languages = Column(JSON, nullable=False, default=list)
    references = Column(JSON, nullable=False, default=list)

    design = Column(JSON, nullable=False, default=dict)
    metadata = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="cv_drafts")
