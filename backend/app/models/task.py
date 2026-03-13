from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    site_name: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)

    task_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False, default="")
    priority: Mapped[str] = mapped_column(String(8), index=True, nullable=False, default="中")
    status: Mapped[str] = mapped_column(String(16), index=True, nullable=False, default="待执行")

    planned_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    planned_end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)

    address: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    remark: Mapped[str] = mapped_column(Text, nullable=False, default="")

    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    assignee = relationship("User", lazy="joined")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), onupdate=func.now(), nullable=False
    )

