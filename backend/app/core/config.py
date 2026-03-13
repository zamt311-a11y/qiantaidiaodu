from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "netopt-tool"
    env: str = "dev"
    secret_key: str = "change-me"

    database_url: str = "sqlite:///../data/app.db"

    amap_web_key: str = ""
    amap_security_js_code: str = ""

    bootstrap_admin_phone: str = ""
    bootstrap_admin_password: str = ""
    bootstrap_admin_name: str = "管理员"

    file_root: str = "../data/files"
    file_dir_task_photos: str = "照片"
    file_dir_kpi: str = "工参"
    file_dir_backups: str = "备份"

    sector_radius_m: int = 50
    sector_angle_deg: int = 60

    def resolve_path(self, rel_or_abs: str) -> Path:
        p = Path(rel_or_abs)
        if p.is_absolute():
            return p
        return (Path(__file__).resolve().parents[3] / rel_or_abs).resolve()

    @property
    def resolved_file_root(self) -> Path:
        return self.resolve_path(self.file_root)

    @property
    def resolved_task_photos_dir(self) -> Path:
        return self.resolved_file_root / self.file_dir_task_photos

    @property
    def resolved_kpi_dir(self) -> Path:
        return self.resolved_file_root / self.file_dir_kpi

    @property
    def resolved_backups_dir(self) -> Path:
        return self.resolved_file_root / self.file_dir_backups


settings = Settings()

