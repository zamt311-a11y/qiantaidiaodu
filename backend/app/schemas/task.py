from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.user import UserOut


class TaskOut(BaseModel):
    id: int
    site_id: str
    site_name: str
    lon: float
    lat: float
    task_type: str
    priority: str
    status: str
    planned_start_at: datetime | None
    planned_end_at: datetime | None
    address: str
    remark: str
    assignee: UserOut | None

    model_config = {"from_attributes": True}


class TaskUpdate(BaseModel):
    status: str | None = None
    remark: str | None = None


class TaskCreate(BaseModel):
    site_id: str
    lon: float
    lat: float
    site_name: str | None = ""
    task_type: str | None = ""
    priority: str | None = "中"
    status: str | None = "待执行"
    planned_start_at: str | None = None
    planned_end_at: str | None = None
    address: str | None = ""
    remark: str | None = ""
    assignee_id: int | None = None


class TaskAdminUpdate(BaseModel):
    site_id: str | None = None
    lon: float | None = None
    lat: float | None = None
    site_name: str | None = None
    task_type: str | None = None
    priority: str | None = None
    status: str | None = None
    planned_start_at: str | None = None
    planned_end_at: str | None = None
    address: str | None = None
    remark: str | None = None
    assignee_id: int | None = None

