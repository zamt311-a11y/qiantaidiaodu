from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings


router = APIRouter()
templates = Jinja2Templates(directory=str((Path(__file__).resolve().parents[1] / "templates").resolve()))
_repo_root = Path(__file__).resolve().parents[3]
_templates_dir = _repo_root / "docs" / "templates"


@router.get("/map", response_class=HTMLResponse)
def admin_map(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "map.html",
        {
            "amap_key": settings.amap_web_key,
            "amap_security_js_code": settings.amap_security_js_code,
        },
    )


@router.get("/import", response_class=HTMLResponse)
def admin_import(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "import.html",
        {
        },
    )


@router.get("/tasks", response_class=HTMLResponse)
def admin_tasks(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "tasks.html",
        {
        },
    )


@router.get("/sectors", response_class=HTMLResponse)
def admin_sectors(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "sectors.html",
        {
        },
    )


@router.get("/users", response_class=HTMLResponse)
def admin_users(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "users.html",
        {
        },
    )


@router.get("/report", response_class=HTMLResponse)
def admin_report(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "report.html",
        {
        },
    )


@router.get("/templates/tasks.csv")
def download_tasks_csv() -> FileResponse:
    path = (_templates_dir / "tasks_template.csv").resolve()
    return FileResponse(path, filename="tasks_template.csv")


@router.get("/templates/tasks.xlsx")
def download_tasks_xlsx() -> FileResponse:
    path = (_templates_dir / "任务.xlsx").resolve()
    return FileResponse(path, filename="任务.xlsx")


@router.get("/templates/sector_4g.csv")
def download_sector_4g_csv() -> FileResponse:
    path = (_templates_dir / "sector_4g_template.csv").resolve()
    return FileResponse(path, filename="sector_4g_template.csv")


@router.get("/templates/sector_5g.csv")
def download_sector_5g_csv() -> FileResponse:
    path = (_templates_dir / "sector_5g_template.csv").resolve()
    return FileResponse(path, filename="sector_5g_template.csv")

