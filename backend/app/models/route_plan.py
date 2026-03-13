from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RoutePlan(Base):
    __tablename__ = "route_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, default="")

    assignee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    assignee = relationship("User", lazy="joined", foreign_keys=[assignee_id])

    task_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

    start_lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    start_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_km: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    creator = relationship("User", lazy="joined", foreign_keys=[created_by])

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)
