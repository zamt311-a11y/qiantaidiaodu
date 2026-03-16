from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.device_token import DeviceToken
from app.models.message import Message
from app.models.user import User
from app.utils.fcm import send_to_tokens as send_fcm_to_tokens
from app.utils.jpush import send_to_tokens as send_jpush_to_tokens


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


def _tokens_for_user(db: Session, user_id: int) -> dict[str, list[str]]:
    rows = db.scalars(select(DeviceToken).where(DeviceToken.user_id == user_id)).all()
    out: dict[str, list[str]] = {"fcm": [], "jpush": []}
    for r in rows:
        if not r or not r.token:
            continue
        platform = (r.platform or "").lower()
        if platform in {"android", "fcm", "firebase"}:
            out["fcm"].append(r.token)
        elif platform == "jpush":
            out["jpush"].append(r.token)
    return out


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
    resp_fcm = send_fcm_to_tokens(tokens["fcm"], title=title, body=content, data=data or {})
    resp_jpush = send_jpush_to_tokens(tokens["jpush"], title=title, body=content, data=data or {})
    return {"fcm": resp_fcm, "jpush": resp_jpush}


def notify_admins(
    db: Session,
    title: str,
    content: str,
    msg_type: str = "system",
    data: dict[str, str] | None = None,
) -> dict:
    admins = db.scalars(select(User).where(User.role.in_(["admin", "super_admin"]))).all()
    tokens: dict[str, list[str]] = {"fcm": [], "jpush": []}
    for u in admins:
        create_message(db, user_id=u.id, title=title, content=content, msg_type=msg_type)
        user_tokens = _tokens_for_user(db, u.id)
        tokens["fcm"].extend(user_tokens["fcm"])
        tokens["jpush"].extend(user_tokens["jpush"])
    return {
        "fcm": send_fcm_to_tokens(tokens["fcm"], title=title, body=content, data=data or {}),
        "jpush": send_jpush_to_tokens(tokens["jpush"], title=title, body=content, data=data or {}),
    }


def notify_engineers(
    db: Session,
    title: str,
    content: str,
    msg_type: str = "system",
    data: dict[str, str] | None = None,
) -> dict:
    engineers = db.scalars(select(User).where(User.role == "engineer")).all()
    tokens: dict[str, list[str]] = {"fcm": [], "jpush": []}
    for u in engineers:
        create_message(db, user_id=u.id, title=title, content=content, msg_type=msg_type)
        user_tokens = _tokens_for_user(db, u.id)
        tokens["fcm"].extend(user_tokens["fcm"])
        tokens["jpush"].extend(user_tokens["jpush"])
    return {
        "fcm": send_fcm_to_tokens(tokens["fcm"], title=title, body=content, data=data or {}),
        "jpush": send_jpush_to_tokens(tokens["jpush"], title=title, body=content, data=data or {}),
    }
