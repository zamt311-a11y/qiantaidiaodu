from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Sector(Base):
    __tablename__ = "sectors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    network: Mapped[str] = mapped_column(String(8), index=True, nullable=False)
    cell_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    lon: Mapped[float] = mapped_column(Float, nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    azimuth_deg: Mapped[float] = mapped_column(Float, nullable=False)

    band: Mapped[str] = mapped_column(String(16), index=True, nullable=False, default="")
    freq: Mapped[str] = mapped_column(String(32), nullable=False, default="")

    raw_fields_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)

