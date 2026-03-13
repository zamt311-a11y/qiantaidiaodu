from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models.route_plan import RoutePlan
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskOut


router = APIRouter()


class RoutePlanCreate(BaseModel):
    assignee_id: int
    task_ids: list[int]
    name: str | None = None
    start_lon: float | None = None
    start_lat: float | None = None
    total_km: float | None = None


def _parse_task_ids(raw: str) -> list[int]:
    try:
        data = json.loads(raw or "[]")
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    out: list[int] = []
    for v in data:
        try:
            out.append(int(v))
        except (TypeError, ValueError):
            continue
    return out


def _plan_to_dict(p: RoutePlan) -> dict:
    ids = _parse_task_ids(p.task_ids_json)
    return {
        "id": p.id,
        "name": p.name,
        "assignee_id": p.assignee_id,
        "assignee": {
            "id": p.assignee.id,
            "name": p.assignee.name,
            "phone": p.assignee.phone,
        } if p.assignee else None,
        "task_ids": ids,
        "task_count": len(ids),
        "start_lon": p.start_lon,
        "start_lat": p.start_lat,
        "total_km": p.total_km,
        "created_by": p.created_by,
        "created_at": p.created_at.isoformat(sep=" ") if isinstance(p.created_at, datetime) else "",
    }


@router.post("", status_code=200)
def create_route_plan(
    payload: RoutePlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    if not payload.task_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="任务列表不能为空")
    assignee = db.get(User, payload.assignee_id)
    if assignee is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="负责人不存在")
    name = (payload.name or "").strip()
    if not name:
        name = f"路线-{datetime.now().strftime('%m%d-%H%M')}"
    plan = RoutePlan(
        name=name,
        assignee_id=assignee.id,
        task_ids_json=json.dumps(payload.task_ids, ensure_ascii=False),
        start_lon=payload.start_lon,
        start_lat=payload.start_lat,
        total_km=payload.total_km,
        created_by=current_user.id,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return _plan_to_dict(plan)


@router.get("")
def list_route_plans(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
    assignee_id: int | None = Query(default=None),
) -> list[dict]:
    stmt = select(RoutePlan)
    if assignee_id is not None:
        stmt = stmt.where(RoutePlan.assignee_id == assignee_id)
    plans = list(db.scalars(stmt.order_by(RoutePlan.id.desc())).all())
    return [_plan_to_dict(p) for p in plans]


@router.get("/my")
def list_my_route_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    stmt = select(RoutePlan).where(RoutePlan.assignee_id == current_user.id)
    plans = list(db.scalars(stmt.order_by(RoutePlan.id.desc())).all())
    return [_plan_to_dict(p) for p in plans]


@router.get("/{plan_id}")
def get_route_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    plan = db.get(RoutePlan, plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="路线不存在")
    if current_user.role != "admin" and plan.assignee_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
    ids = _parse_task_ids(plan.task_ids_json)
    tasks = []
    if ids:
        rows = list(db.scalars(select(Task).where(Task.id.in_(ids))).all())
        by_id = {t.id: t for t in rows}
        for tid in ids:
            t = by_id.get(int(tid))
            if t is not None:
                tasks.append(TaskOut.model_validate(t))
    return {
        "plan": _plan_to_dict(plan),
        "tasks": tasks,
    }
