from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings

router = APIRouter()
templates = Jinja2Templates(directory=str((Path(__file__).resolve().parents[1] / "templates").resolve()))


@router.get("/map", response_class=HTMLResponse)
def mobile_map(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "map.html",
        {
            "amap_key": settings.amap_web_key,
            "amap_security_js_code": settings.amap_security_js_code,
        },
    )


@router.get("/home", response_class=HTMLResponse)
def mobile_home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "mobile_home.html",
        {},
    )

