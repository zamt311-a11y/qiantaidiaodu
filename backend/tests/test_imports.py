from pathlib import Path


def test_admin_map_page(client):
    res = client.get("/admin/map")
    assert res.status_code == 200
    assert "管理端地图" in res.text


def test_mobile_map_page(client):
    res = client.get("/m/map")
    assert res.status_code == 200
    assert "管理端地图" in res.text


def test_mobile_home_page(client):
    res = client.get("/m/home")
    assert res.status_code == 200
    assert "工程师端" in res.text


def test_admin_import_page(client):
    res = client.get("/admin/import")
    assert res.status_code == 200
    assert "导入配置" in res.text


def test_admin_tasks_page(client):
    res = client.get("/admin/tasks")
    assert res.status_code == 200
    assert "任务管理" in res.text


def test_admin_sectors_page(client):
    res = client.get("/admin/sectors")
    assert res.status_code == 200
    assert "工参管理" in res.text


def test_admin_report_page(client):
    res = client.get("/admin/report")
    assert res.status_code == 200
    assert "统计报表" in res.text


def test_list_users_admin(client, admin_token):
    res = client.get("/api/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    users = res.json()
    assert isinstance(users, list)


def test_create_and_delete_task(client, admin_token):
    payload = {
        "site_id": "S900",
        "site_name": "测试站点",
        "lon": 116.397428,
        "lat": 39.90923,
        "task_type": "单验",
        "priority": "中",
        "status": "待执行",
        "address": "北京",
        "remark": "pytest",
    }
    res = client.post(
        "/api/tasks",
        headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
        content=__import__("json").dumps(payload),
    )
    assert res.status_code == 200
    tid = res.json()["id"]

    res2 = client.delete("/api/tasks/%s" % tid, headers={"Authorization": f"Bearer {admin_token}"})
    assert res2.status_code == 200


def test_import_tasks_csv(client, admin_token):
    csv_content = "\n".join(
        [
            "站点ID,站点名称,经度,纬度,任务类型,优先级,状态,计划开始时间,计划完成时间,地址,备注",
            "S001,站点一,116.397428,39.90923,单验,高,待执行,2026-03-12 09:00,2026-03-12 18:00,北京,测试备注",
        ]
    ).encode("utf-8")
    res = client.post(
        "/api/tasks/import",
        headers={"Authorization": f"Bearer {admin_token}"},
        files={"file": ("tasks.csv", csv_content, "text/csv")},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["inserted"] == 1

    res2 = client.get("/api/tasks", headers={"Authorization": f"Bearer {admin_token}"})
    assert res2.status_code == 200
    tasks = res2.json()
    assert len(tasks) == 1
    assert tasks[0]["site_id"] == "S001"


def test_import_tasks_with_mapping(client, admin_token):
    csv_content = "\n".join(
        [
            "站号,经度_站点,纬度_站点,任务内容",
            "S002,116.397428,39.90923,督导",
        ]
    ).encode("utf-8")
    mapping = {
        "site_id": "站号",
        "lon": "经度_站点",
        "lat": "纬度_站点",
        "task_type": "任务内容",
    }
    res = client.post(
        "/api/tasks/import",
        headers={"Authorization": f"Bearer {admin_token}"},
        files={"file": ("tasks2.csv", csv_content, "text/csv"), "mapping_json": (None, __import__("json").dumps(mapping), "text/plain")},
    )
    assert res.status_code == 200
    assert res.json()["inserted"] == 1

    res2 = client.get("/api/tasks", headers={"Authorization": f"Bearer {admin_token}"})
    assert res2.status_code == 200
    assert any(t["site_id"] == "S002" and t["task_type"] == "督导" for t in res2.json())


def test_import_tasks_xlsx_template_and_preview(client, admin_token):
    root = Path(__file__).resolve().parents[2]
    xlsx_path = root / "docs" / "templates" / "任务.xlsx"
    content = xlsx_path.read_bytes()

    prev = client.post(
        "/api/tasks/import/preview",
        headers={"Authorization": f"Bearer {admin_token}"},
        files={"file": (xlsx_path.name, content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert prev.status_code == 200
    data_prev = prev.json()
    assert "站点ID" in data_prev["headers"]
    assert len(data_prev["sample_rows"]) > 0

    res = client.post(
        "/api/tasks/import",
        headers={"Authorization": f"Bearer {admin_token}"},
        files={"file": (xlsx_path.name, content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert res.status_code == 200
    assert res.json()["inserted"] == 5

    res2 = client.get("/api/tasks", headers={"Authorization": f"Bearer {admin_token}"})
    assert res2.status_code == 200
    tasks = res2.json()
    assert any(t["site_id"] == "S001" for t in tasks)


def test_engineer_can_update_status_and_upload_photos(client, admin_token):
    import json

    u = client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
        content=json.dumps({"phone": "13900000001", "name": "工测1", "role": "engineer", "password": "123456"}),
    )
    assert u.status_code == 200
    eng_id = u.json()["id"]

    task_payload = {
        "site_id": "S901",
        "site_name": "外场站点",
        "lon": 116.397428,
        "lat": 39.90923,
        "task_type": "单验",
        "priority": "中",
        "status": "待执行",
        "address": "北京",
        "remark": "",
    }
    t = client.post(
        "/api/tasks",
        headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
        content=json.dumps(task_payload),
    )
    assert t.status_code == 200
    task_id = t.json()["id"]

    d = client.post(
        "/api/tasks/dispatch",
        headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
        content=json.dumps({"task_ids": [task_id], "assignee_id": eng_id}),
    )
    assert d.status_code == 200

    login = client.post(
        "/api/auth/login",
        headers={"Content-Type": "application/json"},
        content=json.dumps({"phone": "13900000001", "password": "123456"}),
    )
    assert login.status_code == 200
    eng_token = login.json()["access_token"]

    up = client.patch(
        f"/api/tasks/{task_id}",
        headers={"Authorization": f"Bearer {eng_token}", "Content-Type": "application/json"},
        content=json.dumps({"status": "执行中", "remark": "已到站"}),
    )
    assert up.status_code == 200
    assert up.json()["status"] == "执行中"
    assert up.json()["remark"] == "已到站"

    photo_bytes = b"\x89PNG\r\n\x1a\n"
    p = client.post(
        f"/api/tasks/{task_id}/photos",
        headers={"Authorization": f"Bearer {eng_token}"},
        files={"files": ("a.png", photo_bytes, "image/png")},
    )
    assert p.status_code == 200
    saved = p.json()["saved"]
    assert isinstance(saved, list) and len(saved) == 1


def test_import_sectors_csv(client, admin_token):
    root = Path(__file__).resolve().parents[2]
    csv_path = root / "4G工参.csv"
    content = csv_path.read_bytes()
    res = client.post(
        "/api/sectors/import",
        headers={"Authorization": f"Bearer {admin_token}"},
        files={"file": (csv_path.name, content, "text/csv")},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["inserted"] > 0

    res2 = client.get("/api/sectors/geojson", headers={"Authorization": f"Bearer {admin_token}"})
    assert res2.status_code == 200
    geo = res2.json()
    assert geo["type"] == "FeatureCollection"
    assert len(geo["features"]) > 0


def test_import_sectors_with_mapping(client, admin_token):
    csv_content = "\n".join(
        [
            "cid,lonX,latX,azi,频段,下行中心频点",
            "C100,116.397428,39.90923,90,78,640000",
        ]
    ).encode("utf-8")
    mapping = {
        "cell_id": "cid",
        "lon": "lonX",
        "lat": "latX",
        "azimuth_deg": "azi",
        "band": "频段",
        "freq": "下行中心频点",
    }
    res = client.post(
        "/api/sectors/import",
        headers={"Authorization": f"Bearer {admin_token}"},
        files={"file": ("sectors2.csv", csv_content, "text/csv"), "mapping_json": (None, __import__("json").dumps(mapping), "text/plain")},
    )
    assert res.status_code == 200
    assert res.json()["inserted"] == 1

    res_list = client.get("/api/sectors/admin_list", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_list.status_code == 200
    items = res_list.json()
    assert isinstance(items, list)
    assert len(items) == 1

    res_purge = client.post(
        "/api/sectors/purge",
        headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
        content=__import__("json").dumps({"network": ["4G"], "band": ["78"], "all": False}),
    )
    assert res_purge.status_code == 200
    assert res_purge.json()["deleted"] == 1

    res3 = client.get("/api/sectors", headers={"Authorization": f"Bearer {admin_token}"})
    assert res3.status_code == 200
    assert res3.json() == []


def test_delete_sector_endpoint(client, admin_token):
    csv_content = "\n".join(
        [
            "cid,lonX,latX,azi,频段,下行中心频点",
            "C101,116.397428,39.90923,90,78,640000",
        ]
    ).encode("utf-8")
    mapping = {"cell_id": "cid", "lon": "lonX", "lat": "latX", "azimuth_deg": "azi", "band": "频段", "freq": "下行中心频点"}
    res = client.post(
        "/api/sectors/import",
        headers={"Authorization": f"Bearer {admin_token}"},
        files={"file": ("sectors3.csv", csv_content, "text/csv"), "mapping_json": (None, __import__("json").dumps(mapping), "text/plain")},
    )
    assert res.status_code == 200
    assert res.json()["inserted"] == 1
    res_list = client.get("/api/sectors/admin_list", headers={"Authorization": f"Bearer {admin_token}"})
    sid = res_list.json()[0]["id"]
    res_del = client.delete(f"/api/sectors/{sid}", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_del.status_code == 200
    assert res_del.json()["deleted"] == 1


def test_bulk_delete_sectors(client, admin_token):
    csv_content = "\n".join(
        [
            "cid,lonX,latX,azi,频段,下行中心频点",
            "C201,116.397428,39.90923,90,78,640000",
            "C202,116.397428,39.90923,120,78,640000",
        ]
    ).encode("utf-8")
    mapping = {"cell_id": "cid", "lon": "lonX", "lat": "latX", "azimuth_deg": "azi", "band": "频段", "freq": "下行中心频点"}
    res = client.post(
        "/api/sectors/import",
        headers={"Authorization": f"Bearer {admin_token}"},
        files={"file": ("sectors4.csv", csv_content, "text/csv"), "mapping_json": (None, __import__("json").dumps(mapping), "text/plain")},
    )
    assert res.status_code == 200
    assert res.json()["inserted"] == 2
    items = client.get("/api/sectors/admin_list", headers={"Authorization": f"Bearer {admin_token}"}).json()
    ids = [x["id"] for x in items]
    res_del = client.post(
        "/api/sectors/bulk_delete",
        headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
        content=__import__("json").dumps({"sector_ids": ids}),
    )
    assert res_del.status_code == 200
    assert res_del.json()["deleted"] == 2
    items2 = client.get("/api/sectors/admin_list", headers={"Authorization": f"Bearer {admin_token}"}).json()
    assert items2 == []


def test_list_sector_bands(client, admin_token):
    res = client.get("/api/sectors/bands", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert isinstance(res.json(), list)

