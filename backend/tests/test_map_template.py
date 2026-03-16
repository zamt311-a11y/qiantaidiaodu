from pathlib import Path


def _read_map_template() -> str:
    root = Path(__file__).resolve().parents[1]
    path = root / "app" / "templates" / "map.html"
    return path.read_text(encoding="utf-8")


def test_map_has_gps_location_logic() -> None:
    html = _read_map_template()
    assert "navigator.geolocation.getCurrentPosition" in html
    assert "AMap.Geolocation" in html
    assert "gpsPos" in html
