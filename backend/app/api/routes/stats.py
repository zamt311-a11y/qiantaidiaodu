from __future__ import annotations

from datetime import datetime, time, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.task import Task
from app.models.user import User


router = APIRouter()


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(value, fmt)
            if fmt == "%Y-%m-%d":
                dt = dt.replace(hour=0, minute=0, second=0)
            return dt
        except ValueError:
            continue
    return None


def _parse_end_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(value, fmt)
            if fmt == "%Y-%m-%d":
                dt = dt.replace(hour=23, minute=59, second=59)
            return dt
        except ValueError:
            continue
    return None


def _resolve_range(days: int, date_from: str | None, date_to: str | None) -> tuple[datetime, datetime, list[str]]:
    now = datetime.now()
    days = max(1, min(int(days or 30), 365))
    df = _parse_dt(date_from)
    dt = _parse_end_dt(date_to)
    if df is None and dt is None:
        end = datetime.combine(now.date(), time(23, 59, 59))
        start = datetime.combine(now.date() - timedelta(days=days - 1), time(0, 0, 0))
    else:
        if df is None:
            df = datetime.combine(now.date() - timedelta(days=days - 1), time(0, 0, 0))
        if dt is None:
            dt = datetime.combine(now.date(), time(23, 59, 59))
        start = df
        end = dt
    if start > end:
        start, end = end, start
    dates = []
    cur = start.date()
    end_date = end.date()
    while cur <= end_date:
        dates.append(cur.isoformat())
        cur = cur + timedelta(days=1)
    return start, end, dates


@router.get("/overview")
def stats_overview(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
    days: int = 30,
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
) -> dict:
    start, end, dates = _resolve_range(days, date_from, date_to)
    basis = func.coalesce(Task.planned_start_at, Task.created_at)

    rows = db.execute(
        select(Task.status, func.count())
        .where(basis >= start, basis <= end)
        .group_by(Task.status)
    ).all()
    status_counts = {str(r[0]): int(r[1] or 0) for r in rows}
    total = sum(status_counts.values())
    completed = status_counts.get("已完成", 0)

    created_rows = db.execute(
        select(func.date(Task.created_at).label("d"), func.count())
        .where(Task.created_at >= start, Task.created_at <= end)
        .group_by("d")
    ).all()
    created_map = {str(r[0]): int(r[1] or 0) for r in created_rows if r[0] is not None}

    done_rows = db.execute(
        select(func.date(Task.updated_at).label("d"), func.count())
        .where(Task.updated_at >= start, Task.updated_at <= end)
        .where(Task.status == "已完成")
        .group_by("d")
    ).all()
    done_map = {str(r[0]): int(r[1] or 0) for r in done_rows if r[0] is not None}

    created_series = [created_map.get(d, 0) for d in dates]
    done_series = [done_map.get(d, 0) for d in dates]

    return {
        "range": {"start": start.isoformat(sep=" "), "end": end.isoformat(sep=" "), "days": len(dates)},
        "total": total,
        "status": status_counts,
        "completion_rate": (completed / total) if total else 0,
        "trend": {"dates": dates, "created": created_series, "completed": done_series},
    }


@router.get("/engineers")
def stats_engineers(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
    days: int = 30,
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
) -> list[dict]:
    start, end, _ = _resolve_range(days, date_from, date_to)
    basis = func.coalesce(Task.planned_start_at, Task.created_at)

    completed = func.sum(case((Task.status == "已完成", 1), else_=0)).label("completed")
    abnormal = func.sum(case((Task.status == "异常", 1), else_=0)).label("abnormal")
    total = func.count().label("total")

    rows = db.execute(
        select(
            User.id,
            User.name,
            User.phone,
            total,
            completed,
            abnormal,
        )
        .select_from(Task)
        .join(User, Task.assignee_id == User.id)
        .where(User.role == "engineer")
        .where(basis >= start, basis <= end)
        .group_by(User.id)
        .order_by(total.desc())
    ).all()

    out: list[dict] = []
    for r in rows:
        t = int(r.total or 0)
        c = int(r.completed or 0)
        b = int(r.abnormal or 0)
        out.append(
            {
                "id": int(r.id),
                "name": r.name or "",
                "phone": r.phone or "",
                "total": t,
                "completed": c,
                "abnormal": b,
                "completion_rate": (c / t) if t else 0,
                "abnormal_rate": (b / t) if t else 0,
            }
        )
    return out
