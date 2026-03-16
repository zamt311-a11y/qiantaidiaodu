from __future__ import annotations

import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.utils.op_log import log_op


router = APIRouter()


class BackupRestoreRequest(BaseModel):
    name: str


def _sqlite_db_path() -> Path:
    url = (settings.database_url or "").strip()
    if not url.startswith("sqlite:"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Backup only supports sqlite.")
    if url in ("sqlite://", "sqlite:///:memory:") or url.endswith(":memory:"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="In-memory sqlite cannot be backed up.")
    if url.startswith("sqlite:////"):
        raw_path = url[len("sqlite:////") :]
        return Path(raw_path)
    if url.startswith("sqlite:///"):
        raw_path = url[len("sqlite:///") :]
        return settings.resolve_path(raw_path)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported sqlite URL format.")


def _list_backup_files(backup_dir: Path) -> list[Path]:
    if not backup_dir.exists():
        return []
    return sorted(
        [p for p in backup_dir.iterdir() if p.is_file() and p.suffix.lower() == ".zip"],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


@router.post("/create", status_code=200)
def create_backup(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    backup_dir = settings.resolved_backups_dir
    backup_dir.mkdir(parents=True, exist_ok=True)

    db_path = _sqlite_db_path()
    if not db_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database file not found.")

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    name = f"backup-{timestamp}.zip"
    backup_path = backup_dir / name

    file_root = settings.resolved_file_root
    file_root.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(backup_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(db_path, arcname=f"db/{db_path.name}")
        if file_root.exists():
            for p in file_root.rglob("*"):
                if not p.is_file():
                    continue
                if p.is_relative_to(backup_dir):
                    continue
                arcname = f"files/{p.relative_to(file_root)}"
                zf.write(p, arcname=arcname)

    log_op(db, current_user.id, "backup.create", f"name={name}")
    db.commit()

    stat = backup_path.stat()
    return {
        "name": name,
        "size": stat.st_size,
        "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(sep=" "),
    }


@router.get("", status_code=200)
def list_backups(
    _: Session = Depends(get_db),
    __: User = Depends(require_admin),
) -> list[dict]:
    backup_dir = settings.resolved_backups_dir
    items: list[dict] = []
    for p in _list_backup_files(backup_dir):
        stat = p.stat()
        items.append(
            {
                "name": p.name,
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(sep=" "),
            }
        )
    return items


@router.post("/restore", status_code=200)
def restore_backup(
    payload: BackupRestoreRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    backup_dir = settings.resolved_backups_dir
    backup_path = backup_dir / payload.name
    if not backup_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup file not found.")

    db_path = _sqlite_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    file_root = settings.resolved_file_root
    file_root.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        with zipfile.ZipFile(backup_path, "r") as zf:
            zf.extractall(tmp_path)

        db_dir = tmp_path / "db"
        db_files = [p for p in db_dir.iterdir() if p.is_file()] if db_dir.exists() else []
        if not db_files:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Backup missing database file.")
        shutil.copy2(db_files[0], db_path)

        files_dir = tmp_path / "files"
        if files_dir.exists():
            for p in files_dir.rglob("*"):
                if not p.is_file():
                    continue
                dest = file_root / p.relative_to(files_dir)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, dest)

    log_op(db, current_user.id, "backup.restore", f"name={payload.name}")
    db.commit()
    return {"restored": True, "name": payload.name}
