from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.device_token import DeviceToken
from app.models.message import Message
from app.models.user import User
from app.utils.fcm import send_to_tokens


def create_message(
    db: Session,
    user_id: int,
    title: str,
    content: str,
    msg_type: str = "system",
) -> Message:
    msg = Message(user_id=user_id, title=title, content=content, msg_type=msg_type)
    db.add(msg)
    return msg


def _tokens_for_user(db: Session, user_id: int) -> list[str]:
    rows = db.scalars(select(DeviceToken).where(DeviceToken.user_id == user_id)).all()
    return [r.token for r in rows if r and r.token]


def notify_user(
    db: Session,
    user_id: int,
    title: str,
    content: str,
    msg_type: str = "system",
    data: dict[str, str] | None = None,
) -> dict:
    create_message(db, user_id=user_id, title=title, content=content, msg_type=msg_type)
    tokens = _tokens_for_user(db, user_id)
    resp = send_to_tokens(tokens, title=title, body=content, data=data or {})
    return resp


def notify_admins(
    db: Session,
    title: str,
    content: str,
    msg_type: str = "system",
    data: dict[str, str] | None = None,
) -> dict:
    admins = db.scalars(select(User).where(User.role.in_(["admin", "super_admin"]))).all()
    tokens: list[str] = []
    for u in admins:
        create_message(db, user_id=u.id, title=title, content=content, msg_type=msg_type)
        tokens.extend(_tokens_for_user(db, u.id))
    return send_to_tokens(tokens, title=title, body=content, data=data or {})


def notify_engineers(
    db: Session,
    title: str,
    content: str,
    msg_type: str = "system",
    data: dict[str, str] | None = None,
) -> dict:
    engineers = db.scalars(select(User).where(User.role == "engineer")).all()
    tokens: list[str] = []
    for u in engineers:
        create_message(db, user_id=u.id, title=title, content=content, msg_type=msg_type)
        tokens.extend(_tokens_for_user(db, u.id))
    return send_to_tokens(tokens, title=title, body=content, data=data or {})
