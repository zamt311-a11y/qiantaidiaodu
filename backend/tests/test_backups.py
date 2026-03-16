from app.core.config import settings


def test_backup_create_list_restore(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    res = client.post("/api/backups/create", headers=headers)
    assert res.status_code == 200
    name = res.json()["name"]

    backup_path = settings.resolved_backups_dir / name
    assert backup_path.exists()

    res2 = client.get("/api/backups", headers=headers)
    assert res2.status_code == 200
    names = [item["name"] for item in res2.json()]
    assert name in names

    res3 = client.post("/api/backups/restore", headers=headers, json={"name": name})
    assert res3.status_code == 200
    assert res3.json()["restored"] is True
