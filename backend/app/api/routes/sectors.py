from __future__ import annotations

import csv
import io
import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.config import settings
from app.db.session import get_db
from app.models.sector import Sector
from app.models.task import Task
from app.models.user import User
from app.schemas.sector import SectorListItem, SectorOut
from app.schemas.task import TaskOut
from app.utils.geo import haversine_distance_m, point_in_polygon, sector_polygon


router = APIRouter()


class ImportErrorItem(BaseModel):
    row: int
    error: str


class SectorPurgeRequest(BaseModel):
    network: list[str] = []
    band: list[str] = []
    all: bool = False


class SectorBulkDeleteRequest(BaseModel):
    sector_ids: list[int]


def _norm_header(s: str) -> str:
    return "".join(ch for ch in s.strip().lower().replace(" ", "").replace("_", "") if ch not in "\ufeff")


def _infer_network(headers_norm: list[str]) -> str:
    for h in headers_norm:
        if "ssb" in h or "nrarfcn" in h:
            return "5G"
    for h in headers_norm:
        if "天线经度" in h or "天线纬度" in h:
            return "5G"
    return "4G"


def _pick(row: dict[str, str], keys: list[str]) -> str | None:
    for k in keys:
        if k in row and row[k] not in (None, ""):
            return str(row[k]).strip()
    return None


def _color_for(network: str, band: str) -> str:
    if network == "4G":
        return {"1": "#ff3b30", "3": "#007aff", "5": "#34c759", "8": "#8e8e93"}.get(band, "#007aff")
    return {"1": "#ff9500", "5": "#af52de", "78": "#00c7be", "79": "#636366"}.get(band, "#ff9500")


@router.get("", response_model=list[SectorOut])
def list_sectors(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
    network: list[str] = Query(default=[]),
    band: list[str] = Query(default=[]),
) -> list[SectorOut]:
    stmt = select(Sector)
    if network:
        stmt = stmt.where(Sector.network.in_(network))
    if band:
        stmt = stmt.where(Sector.band.in_(band))
    sectors = list(db.scalars(stmt.order_by(Sector.id.desc())).all())
    return [SectorOut.model_validate(s) for s in sectors]


@router.get("/geojson")
def sectors_geojson(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
    network: list[str] = Query(default=[]),
    band: list[str] = Query(default=[]),
    radius_m: int | None = None,
    min_lng: float | None = None,
    min_lat: float | None = None,
    max_lng: float | None = None,
    max_lat: float | None = None,
    limit: int = 2000,
) -> dict:
    stmt = select(Sector)
    if network:
        stmt = stmt.where(Sector.network.in_(network))
    if band:
        stmt = stmt.where(Sector.band.in_(band))
    if min_lng is not None and min_lat is not None and max_lng is not None and max_lat is not None:
        stmt = stmt.where(Sector.lon >= min_lng, Sector.lon <= max_lng, Sector.lat >= min_lat, Sector.lat <= max_lat)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    if limit < 1:
        limit = 1
    if limit > 5000:
        limit = 5000
    sectors = list(db.scalars(stmt.limit(limit)).all())
    r = float(radius_m or settings.sector_radius_m)
    features: list[dict] = []
    for s in sectors:
        coords = sector_polygon(s.lat, s.lon, s.azimuth_deg, r, angle_deg=float(settings.sector_angle_deg))
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [coords]},
                "properties": {
                    "id": s.id,
                    "network": s.network,
                    "band": s.band,
                    "cell_id": s.cell_id,
                    "color": _color_for(s.network, s.band),
                },
            }
        )
    return {
        "type": "FeatureCollection",
        "features": features,
        "meta": {"total": total, "returned": len(features), "truncated": len(features) < total},
    }


@router.get("/extent")
def sectors_extent(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
    network: list[str] = Query(default=[]),
    band: list[str] = Query(default=[]),
) -> dict:
    stmt = select(Sector)
    if network:
        stmt = stmt.where(Sector.network.in_(network))
    if band:
        stmt = stmt.where(Sector.band.in_(band))
    q = stmt.subquery()
    row = db.execute(
        select(
            func.count().label("count"),
            func.min(q.c.lon).label("min_lng"),
            func.min(q.c.lat).label("min_lat"),
            func.max(q.c.lon).label("max_lng"),
            func.max(q.c.lat).label("max_lat"),
        )
    ).one()
    return {
        "count": int(row.count or 0),
        "min_lng": row.min_lng,
        "min_lat": row.min_lat,
        "max_lng": row.max_lng,
        "max_lat": row.max_lat,
    }


@router.get("/bands", response_model=list[str])
def list_sector_bands(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
    network: list[str] = Query(default=[]),
) -> list[str]:
    stmt = select(func.distinct(Sector.band)).where(Sector.band != "")
    if network:
        stmt = stmt.where(Sector.network.in_(network))
    rows = list(db.execute(stmt).all())
    bands = sorted({str(r[0]).strip() for r in rows if r and r[0] is not None and str(r[0]).strip() != ""})
    return bands


@router.post("/import")
def import_sectors(
    file: UploadFile = File(...),
    mapping_json: str | None = Form(default=None),
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
) -> dict:
    content = file.file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("gb18030")
    f = io.StringIO(text)
    reader = csv.DictReader(f)
    if reader.fieldnames is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件为空或无表头")

    norm_to_original: dict[str, str] = {_norm_header(h): h for h in reader.fieldnames}
    headers_norm = list(norm_to_original.keys())
    network = _infer_network(headers_norm)

    default_lon_4g = ["站点经度", "经度", "lon", "longitude", "lng"]
    default_lat_4g = ["站点纬度", "纬度", "lat", "latitude"]
    default_lon_5g = ["天线经度", "经度", "lon", "longitude", "lng"]
    default_lat_5g = ["天线纬度", "纬度", "lat", "latitude"]
    default_azimuth = ["方向角", "方位角", "azimuth", "bearing"]
    default_cellid = ["cellid", "小区id", "小区标识", "扇区标识"]
    default_band = ["频段", "band"]
    default_freq = ["ssb频点", "中心频点", "下行链路的中心频点", "下行中心频点", "freq"]

    mapping: dict[str, str] = {}
    if mapping_json:
        try:
            mapping = json.loads(mapping_json)
        except json.JSONDecodeError:
            mapping = {}
    if not isinstance(mapping, dict):
        mapping = {}

    def k(field: str, fallback: list[str]) -> list[str]:
        v = mapping.get(field)
        if isinstance(v, str) and v.strip():
            return [_norm_header(v)]
        return [_norm_header(x) for x in fallback]

    keys_lon = k("lon", default_lon_5g if network == "5G" else default_lon_4g)
    keys_lat = k("lat", default_lat_5g if network == "5G" else default_lat_4g)
    keys_azimuth = k("azimuth_deg", default_azimuth)
    keys_cellid = k("cell_id", default_cellid)
    keys_band = k("band", default_band)
    keys_freq = k("freq", default_freq)

    errors: list[ImportErrorItem] = []
    inserted = 0

    for idx, row in enumerate(reader, start=2):
        row_norm: dict[str, str] = {}
        for nk, ok in norm_to_original.items():
            v = row.get(ok)
            row_norm[nk] = "" if v is None else str(v).strip()

        cell_id = _pick(row_norm, keys_cellid)
        lon_s = _pick(row_norm, keys_lon)
        lat_s = _pick(row_norm, keys_lat)
        azi_s = _pick(row_norm, keys_azimuth)
        if not cell_id:
            errors.append(ImportErrorItem(row=idx, error="缺少CELLID"))
            continue
        try:
            lon = float(lon_s) if lon_s is not None else None
            lat = float(lat_s) if lat_s is not None else None
            azimuth = float(azi_s) if azi_s is not None else None
        except ValueError:
            lon = None
            lat = None
            azimuth = None
        if lon is None or lat is None or azimuth is None:
            errors.append(ImportErrorItem(row=idx, error="经纬度或方位角格式错误"))
            continue

        band_v = _pick(row_norm, keys_band) or ""
        freq_v = _pick(row_norm, keys_freq) or ""
        raw_json = json.dumps(row, ensure_ascii=False)
        db.add(
            Sector(
                network=network,
                cell_id=cell_id,
                lon=lon,
                lat=lat,
                azimuth_deg=azimuth,
                band=band_v,
                freq=freq_v,
                raw_fields_json=raw_json,
            )
        )
        inserted += 1

    db.commit()
    return {"network": network, "inserted": inserted, "errors": [e.model_dump() for e in errors]}


@router.post("/purge")
def purge_sectors(
    payload: SectorPurgeRequest,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
) -> dict:
    if not payload.all and not payload.network and not payload.band:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="未指定过滤条件；清空全部请传 all=true")
    stmt = select(func.count()).select_from(Sector)
    if payload.network:
        stmt = stmt.where(Sector.network.in_(payload.network))
    if payload.band:
        stmt = stmt.where(Sector.band.in_(payload.band))
    total = int(db.scalar(stmt) or 0)
    d = delete(Sector)
    if payload.network:
        d = d.where(Sector.network.in_(payload.network))
    if payload.band:
        d = d.where(Sector.band.in_(payload.band))
    db.execute(d)
    db.commit()
    return {"deleted": total}


@router.get("/admin_list", response_model=list[SectorListItem])
def admin_list_sectors(
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
    network: list[str] = Query(default=[]),
    band: list[str] = Query(default=[]),
    q: str | None = None,
    offset: int = 0,
    limit: int = 200,
) -> list[SectorListItem]:
    stmt = select(Sector)
    if network:
        stmt = stmt.where(Sector.network.in_(network))
    if band:
        stmt = stmt.where(Sector.band.in_(band))
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Sector.cell_id.ilike(like), Sector.raw_fields_json.ilike(like)))
    if offset < 0:
        offset = 0
    if limit < 1:
        limit = 1
    if limit > 1000:
        limit = 1000
    sectors = list(db.scalars(stmt.order_by(Sector.id.desc()).offset(offset).limit(limit)).all())

    items: list[SectorListItem] = []
    for s in sectors:
        cell_name: str | None = None
        try:
            raw = json.loads(s.raw_fields_json) if s.raw_fields_json else None
            if isinstance(raw, dict):
                cell_name = raw.get("小区名称") or raw.get("小区名") or raw.get("CELLNAME") or raw.get("cellname")
        except Exception:
            cell_name = None
        items.append(
            SectorListItem(
                id=s.id,
                network=s.network,
                cell_id=s.cell_id,
                cell_name=cell_name,
                lon=s.lon,
                lat=s.lat,
                azimuth_deg=s.azimuth_deg,
                band=s.band,
                freq=s.freq,
            )
        )
    return items


@router.delete("/{sector_id}")
def delete_sector(
    sector_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
) -> dict:
    sector = db.get(Sector, sector_id)
    if sector is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="扇区不存在")
    db.delete(sector)
    db.commit()
    return {"deleted": 1}


@router.post("/bulk_delete")
def bulk_delete_sectors(
    payload: SectorBulkDeleteRequest,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
) -> dict:
    if not payload.sector_ids:
        return {"deleted": 0}
    sectors = list(db.scalars(select(Sector).where(Sector.id.in_(payload.sector_ids))).all())
    for s in sectors:
        db.delete(s)
    db.commit()
    return {"deleted": len(sectors)}


@router.get("/{sector_id}", response_model=SectorOut)
def get_sector(
    sector_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
) -> SectorOut:
    sector = db.get(Sector, sector_id)
    if sector is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="扇区不存在")
    return SectorOut.model_validate(sector)


@router.get("/{sector_id}/related_tasks", response_model=list[TaskOut])
def related_tasks(
    sector_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    radius_m: int | None = None,
    limit: int = 500,
) -> list[TaskOut]:
    sector = db.get(Sector, sector_id)
    if sector is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="扇区不存在")
    r = float(radius_m or settings.sector_radius_m)
    poly = sector_polygon(sector.lat, sector.lon, sector.azimuth_deg, r, angle_deg=float(settings.sector_angle_deg))
    min_lng = min(p[0] for p in poly)
    max_lng = max(p[0] for p in poly)
    min_lat = min(p[1] for p in poly)
    max_lat = max(p[1] for p in poly)

    stmt = select(Task).where(Task.lon >= min_lng, Task.lon <= max_lng, Task.lat >= min_lat, Task.lat <= max_lat)
    if current_user.role != "admin":
        stmt = stmt.where(Task.assignee_id == current_user.id)
    stmt = stmt.order_by(Task.id.desc())
    if limit < 1:
        limit = 1
    if limit > 2000:
        limit = 2000
    candidates = list(db.scalars(stmt.limit(limit)).all())

    tasks = [
        t
        for t in candidates
        if haversine_distance_m(sector.lat, sector.lon, t.lat, t.lon) <= r + 5.0 and point_in_polygon(t.lon, t.lat, poly)
    ]
    return [TaskOut.model_validate(t) for t in tasks]

