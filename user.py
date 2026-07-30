from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class User(Base):
    """
    Simplified production User model showing the CV Studio relationship.
    Merge this into your existing User model instead of replacing it.
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    # ===== CV Studio Relationship =====
    cv_drafts = relationship(
        "CVDraft",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="CVDraft.updated_at.desc()",
    )
