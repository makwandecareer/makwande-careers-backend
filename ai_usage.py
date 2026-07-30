from __future__ import annotations

from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AIUsage(Base):
    """
    Tracks AI feature usage for analytics, billing, and monitoring.
    """

    __tablename__ = "ai_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    feature: Mapped[str] = mapped_column(String(100), index=True)
    model: Mapped[str] = mapped_column(String(100), default="gpt-5.5")

    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)

    estimated_cost_cents: Mapped[int] = mapped_column(Integer, default=0)
    processing_time_ms: Mapped[int] = mapped_column(Integer, default=0)

    status: Mapped[str] = mapped_column(String(30), default="success")
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
