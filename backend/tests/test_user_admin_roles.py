import json


def _login(client, phone: str, password: str) -> str:
    res = client.post(
        "/api/auth/login",
        headers={"Content-Type": "application/json"},
        content=json.dumps({"phone": phone, "password": password}),
    )
    assert res.status_code == 200
    return res.json()["access_token"]


def test_super_admin_can_create_admin(client, admin_token):
    res = client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
        content=json.dumps({"phone": "13800000001", "name": "管理员1", "role": "admin", "password": "pass123"}),
    )
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "admin"


def test_admin_cannot_create_admin(client, admin_token):
    # create admin user first
    res = client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
        content=json.dumps({"phone": "13800000002", "name": "管理员2", "role": "admin", "password": "pass123"}),
    )
    assert res.status_code == 200
    admin_login = _login(client, "13800000002", "pass123")

    res2 = client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_login}", "Content-Type": "application/json"},
        content=json.dumps({"phone": "13800000003", "name": "管理员3", "role": "admin", "password": "pass123"}),
    )
    assert res2.status_code == 403


def test_admin_can_create_engineer(client, admin_token):
    res = client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
        content=json.dumps({"phone": "13800000004", "name": "管理员4", "role": "admin", "password": "pass123"}),
    )
    assert res.status_code == 200
    admin_login = _login(client, "13800000004", "pass123")

    res2 = client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_login}", "Content-Type": "application/json"},
        content=json.dumps({"phone": "13900000004", "name": "工程师1", "role": "engineer", "password": "pass123"}),
    )
    assert res2.status_code == 200
    assert res2.json()["role"] == "engineer"


def test_admin_cannot_manage_admin_user(client, admin_token):
    # super admin creates admin
    res = client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
        content=json.dumps({"phone": "13800000005", "name": "管理员5", "role": "admin", "password": "pass123"}),
    )
    assert res.status_code == 200
    target_id = res.json()["id"]
    admin_login = _login(client, "13800000005", "pass123")

    res2 = client.patch(
        f"/api/users/{target_id}",
        headers={"Authorization": f"Bearer {admin_login}", "Content-Type": "application/json"},
        content=json.dumps({"name": "修改失败"}),
    )
    assert res2.status_code == 403


def test_super_admin_can_reset_password(client, admin_token):
    res = client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
        content=json.dumps({"phone": "13900000005", "name": "工程师2", "role": "engineer", "password": "pass123"}),
    )
    assert res.status_code == 200
    uid = res.json()["id"]

    reset = client.post(
        f"/api/users/{uid}/reset_password",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert reset.status_code == 200
    new_pwd = reset.json().get("password")
    assert isinstance(new_pwd, str) and new_pwd

    new_token = _login(client, "13900000005", new_pwd)
    assert new_token


def test_admin_cannot_reset_super_admin_password(client, admin_token):
    res = client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
        content=json.dumps({"phone": "13800000006", "name": "管理员6", "role": "admin", "password": "pass123"}),
    )
    assert res.status_code == 200
    admin_login = _login(client, "13800000006", "pass123")

    reset = client.post(
        "/api/users/1/reset_password",
        headers={"Authorization": f"Bearer {admin_login}"},
    )
    assert reset.status_code == 403

