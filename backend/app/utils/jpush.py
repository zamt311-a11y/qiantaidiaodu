from __future__ import annotations

import base64
from typing import Any

import httpx

from app.core.config import settings


def send_to_tokens(tokens: list[str], title: str, body: str, data: dict[str, str] | None = None) -> dict[str, Any]:
    clean = [t for t in tokens if t]
    if not clean:
        return {"success": 0, "failure": 0, "skipped": "no_tokens"}
    if not settings.jpush_enabled:
        return {"success": 0, "failure": 0, "skipped": "disabled"}
    if not settings.jpush_app_key or not settings.jpush_master_secret:
        return {"success": 0, "failure": 0, "skipped": "missing_credentials"}

    payload = {
        "platform": "android",
        "audience": {"registration_id": clean},
        "notification": {
            "alert": body,
            "android": {
                "alert": body,
                "title": title,
                "extras": {str(k): str(v) for k, v in (data or {}).items()},
            },
        },
    }
    token = f"{settings.jpush_app_key}:{settings.jpush_master_secret}".encode("utf-8")
    auth = base64.b64encode(token).decode("utf-8")
    headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/json"}

    try:
        resp = httpx.post("https://api.jpush.cn/v3/push", json=payload, headers=headers, timeout=10.0)
        info = {}
        try:
            info = resp.json()
        except Exception:
            info = {"text": resp.text}
        return {"success": 1 if resp.status_code < 400 else 0, "status_code": resp.status_code, "response": info}
    except Exception as exc:
        return {"success": 0, "failure": 1, "error": str(exc)}
