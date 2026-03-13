from __future__ import annotations

from pydantic import BaseModel


class SectorOut(BaseModel):
    id: int
    network: str
    cell_id: str
    lon: float
    lat: float
    azimuth_deg: float
    band: str
    freq: str
    raw_fields_json: str

    model_config = {"from_attributes": True}


class SectorListItem(BaseModel):
    id: int
    network: str
    cell_id: str
    cell_name: str | None = None
    lon: float
    lat: float
    azimuth_deg: float
    band: str
    freq: str

    model_config = {"from_attributes": True}

