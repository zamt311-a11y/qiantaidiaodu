from pathlib import Path


def _read_map_template() -> str:
    root = Path(__file__).resolve().parents[1]
    path = root / "app" / "templates" / "map.html"
    return path.read_text(encoding="utf-8")


def test_map_has_route_layer_toggles() -> None:
    html = _read_map_template()
    assert 'id="routeTogglePlan"' in html
    assert 'id="routeToggleMy"' in html


def test_map_task_action_has_submit_cancel() -> None:
    html = _read_map_template()
    assert 'id="taskActionSubmit"' in html
    assert 'id="taskActionCancel"' in html
