from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class UserOut(BaseModel):
    id: int
    phone: str
    name: str
    role: str
    is_active: bool | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    phone: str
    name: str
    role: str | None = "engineer"
    password: str


class UserAdminUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    password: str | None = None
    is_active: bool | None = None

