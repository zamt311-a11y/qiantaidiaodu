from __future__ import annotations

from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    import firebase_admin

from app.core.config import settings


def _ensure_app() -> Any:
    if settings.fcm_dry_run:
        return None
    import firebase_admin
    from firebase_admin import credentials

    if firebase_admin._apps:
        return firebase_admin.get_app()
    path = (settings.fcm_service_account_path or "").strip()
    if not path:
        raise RuntimeError("FCM service account path missing")
    if not Path(path).exists():
        raise RuntimeError("FCM service account file not found")
    cred = credentials.Certificate(path)
    return firebase_admin.initialize_app(cred)


def send_to_tokens(
    tokens: list[str],
    title: str,
    body: str,
    data: dict[str, str] | None = None,
) -> dict[str, Any]:
    if not tokens:
        return {"success": 0, "failure": 0, "dry_run": settings.fcm_dry_run}
    if settings.fcm_dry_run:
        return {"success": len(tokens), "failure": 0, "dry_run": True}
    from firebase_admin import messaging

    app = _ensure_app()
    msg = messaging.MulticastMessage(
        tokens=tokens,
        notification=messaging.Notification(title=title, body=body),
        data=data or {},
    )
    resp = messaging.send_multicast(msg, app=app, dry_run=False)
    return {
        "success": resp.success_count,
        "failure": resp.failure_count,
        "dry_run": False,
    }
