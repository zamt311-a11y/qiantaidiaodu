from __future__ import annotations

from app.models.op_log import OpLog


def log_op(db, user_id: int | None, action: str, detail: str) -> None:
    op = OpLog(user_id=user_id, action=action or "", detail=detail or "")
    db.add(op)
