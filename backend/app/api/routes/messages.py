from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.device_token import DeviceToken
from app.models.message import Message
from app.models.user import User


router = APIRouter()


class DeviceTokenIn(BaseModel):
    token: str
    platform: str = "android"


class MarkReadRequest(BaseModel):
    message_ids: list[int] = []


class MessageOut(BaseModel):
    id: int
    title: str
    content: str
    msg_type: str
    read_at: str | None
    created_at: str


@router.post("/device_tokens")
def register_device_token(
    payload: DeviceTokenIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    token_value = (payload.token or "").strip()
    if not token_value:
        return {"updated": 0, "reason": "token empty"}
    device = db.scalar(select(DeviceToken).where(DeviceToken.token == token_value))
    if device is None:
        device = DeviceToken(user_id=current_user.id, token=token_value, platform=payload.platform or "android")
        db.add(device)
    else:
        device.user_id = current_user.id
        device.platform = payload.platform or device.platform or "android"
        db.add(device)
    db.commit()
    return {"updated": 1}


@router.get("")
def list_messages(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    unread: bool | None = Query(default=None),
    offset: int = 0,
    limit: int = 100,
) -> list[MessageOut]:
    stmt = select(Message).where(Message.user_id == current_user.id)
    if unread is True:
        stmt = stmt.where(Message.read_at.is_(None))
    if offset < 0:
        offset = 0
    if limit < 1:
        limit = 1
    if limit > 500:
        limit = 500
    rows = list(db.scalars(stmt.order_by(Message.id.desc()).offset(offset).limit(limit)).all())
    out: list[MessageOut] = []
    for m in rows:
        out.append(
            MessageOut(
                id=int(m.id),
                title=m.title,
                content=m.content,
                msg_type=m.msg_type,
                read_at=m.read_at.isoformat(sep=" ") if m.read_at else None,
                created_at=m.created_at.isoformat(sep=" "),
            )
        )
    return out


@router.post("/mark_read")
def mark_read(
    payload: MarkReadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    now = datetime.utcnow()
    if payload.message_ids:
        stmt = select(Message).where(Message.user_id == current_user.id, Message.id.in_(payload.message_ids))
    else:
        stmt = select(Message).where(Message.user_id == current_user.id, Message.read_at.is_(None))
    rows = list(db.scalars(stmt).all())
    for m in rows:
        m.read_at = now
        db.add(m)
    db.commit()
    return {"updated": len(rows)}


@router.get("/unread_count")
def unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    count = db.scalar(
        select(func.count()).select_from(Message).where(Message.user_id == current_user.id, Message.read_at.is_(None))
    )
    return {"count": int(count or 0)}
