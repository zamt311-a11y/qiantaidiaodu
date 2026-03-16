from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.op_log import OpLog


def test_op_log_on_task_dispatch(client, admin_token):
    import json

    u = client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
        content=json.dumps({"phone": "13900000002", "name": "测2", "role": "engineer", "password": "123456"}),
    )
    assert u.status_code == 200
    eng_id = u.json()["id"]

    t = client.post(
        "/api/tasks",
        headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
        content=json.dumps(
            {
                "site_id": "S910",
                "site_name": "日志测试",
                "lon": 116.397428,
                "lat": 39.90923,
                "task_type": "单验",
                "priority": "中",
                "status": "待执行",
                "address": "北京",
                "remark": "",
            }
        ),
    )
    assert t.status_code == 200
    task_id = t.json()["id"]

    d = client.post(
        "/api/tasks/dispatch",
        headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
        content=json.dumps({"task_ids": [task_id], "assignee_id": eng_id}),
    )
    assert d.status_code == 200

    with SessionLocal() as db:
        row = db.scalar(select(OpLog).where(OpLog.action == "task.dispatch").order_by(OpLog.id.desc()))
        assert row is not None
