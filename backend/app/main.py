from __future__ import annotations

import logging
import socket
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.admin.routes import router as admin_router
from app.api.router import api_router
from app.mobile.routes import router as mobile_router
from app.core.config import settings
from app.db.init_db import bootstrap_admin, init_db
from app.db.session import SessionLocal


logging.getLogger("passlib.handlers.bcrypt").setLevel(logging.ERROR)


def _ensure_sqlite_db_parent_dir() -> None:
    url = (settings.database_url or "").strip()
    if not url.startswith("sqlite:"):
        return
    if url == "sqlite://":
        return
    if url.endswith(":memory:"):
        return

    if url.startswith("sqlite:////"):
        raw_path = url[len("sqlite:////") :]
        db_path = Path(raw_path)
    elif url.startswith("sqlite:///"):
        raw_path = url[len("sqlite:///") :]
        db_path = settings.resolve_path(raw_path)
    else:
        return

    db_path.parent.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _ensure_sqlite_db_parent_dir()
    settings.resolved_task_photos_dir.mkdir(parents=True, exist_ok=True)
    settings.resolved_kpi_dir.mkdir(parents=True, exist_ok=True)
    settings.resolved_backups_dir.mkdir(parents=True, exist_ok=True)
    init_db()
    if settings.bootstrap_admin_phone and settings.bootstrap_admin_password:
        db = SessionLocal()
        try:
            bootstrap_admin(
                db,
                phone=settings.bootstrap_admin_phone,
                password=settings.bootstrap_admin_password,
                name=settings.bootstrap_admin_name,
            )
        finally:
            db.close()

    try:
        hostname = socket.gethostname()
        # Windows下获取所有网卡IP
        _, _, ip_list = socket.gethostbyname_ex(hostname)
        print("\n" + "=" * 50)
        print("🚀 服务启动成功！")
        print(f"👉 本机访问: http://localhost:8000")
        for ip in ip_list:
            if not ip.startswith("127."):
                print(f"👉 局域网访问: http://{ip}:8000")
        print("=" * 50 + "\n")
    except Exception:
        pass

    yield


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api")
    app.include_router(admin_router, prefix="/admin")
    app.include_router(mobile_router, prefix="/m")

    @app.get("/health")
    def health() -> dict:
        return {"ok": True, "env": settings.env}

    return app


app = create_app()

