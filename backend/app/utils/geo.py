from __future__ import annotations

import math


EARTH_RADIUS_M = 6371000.0


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1r = math.radians(lat1)
    lon1r = math.radians(lon1)
    lat2r = math.radians(lat2)
    lon2r = math.radians(lon2)
    dlat = lat2r - lat1r
    dlon = lon2r - lon1r
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1r) * math.cos(lat2r) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_M * c


def destination_point(lat: float, lon: float, bearing_deg: float, distance_m: float) -> tuple[float, float]:
    bearing = math.radians(bearing_deg)
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)
    dr = distance_m / EARTH_RADIUS_M
    lat2 = math.asin(math.sin(lat1) * math.cos(dr) + math.cos(lat1) * math.sin(dr) * math.cos(bearing))
    lon2 = lon1 + math.atan2(
        math.sin(bearing) * math.sin(dr) * math.cos(lat1),
        math.cos(dr) - math.sin(lat1) * math.sin(lat2),
    )
    return (math.degrees(lat2), math.degrees(lon2))


def sector_polygon(
    lat: float,
    lon: float,
    azimuth_deg: float,
    radius_m: float,
    angle_deg: float = 60.0,
    points: int = 8,
) -> list[tuple[float, float]]:
    half = angle_deg / 2.0
    start = azimuth_deg - half
    end = azimuth_deg + half
    coords: list[tuple[float, float]] = [(lon, lat)]
    if points < 2:
        points = 2
    step = (end - start) / (points - 1)
    for i in range(points):
        bearing = start + step * i
        plat, plon = destination_point(lat, lon, bearing, radius_m)
        coords.append((plon, plat))
    coords.append((lon, lat))
    return coords


def point_in_polygon(lon: float, lat: float, polygon: list[tuple[float, float]]) -> bool:
    if not polygon or len(polygon) < 3:
        return False
    inside = False
    j = len(polygon) - 1
    for i in range(len(polygon)):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        intersect = (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-12) + xi
        if intersect:
            inside = not inside
        j = i
    return inside

