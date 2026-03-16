from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.device_token import DeviceToken
from app.models.message import Message
from app.models.user import User


def _get_admin_user_id() -> int:
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.phone == "13800000000"))
        assert user is not None
        return int(user.id)


def test_register_device_token(client, admin_token):
    res = client.post(
        "/api/messages/device_tokens",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"token": "tok-1", "platform": "android"},
    )
    assert res.status_code == 200
    with SessionLocal() as db:
        token = db.scalar(select(DeviceToken).where(DeviceToken.token == "tok-1"))
        assert token is not None


def test_list_and_mark_read_messages(client, admin_token):
    user_id = _get_admin_user_id()
    with SessionLocal() as db:
        msg = Message(user_id=user_id, title="t1", content="c1", msg_type="system")
        db.add(msg)
        db.commit()
        mid = int(msg.id)

    res = client.get("/api/messages?unread=true", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert any(m["id"] == mid for m in data)

    res2 = client.post(
        "/api/messages/mark_read",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"message_ids": [mid]},
    )
    assert res2.status_code == 200
    assert res2.json()["updated"] == 1

    res3 = client.get("/api/messages/unread_count", headers={"Authorization": f"Bearer {admin_token}"})
    assert res3.status_code == 200
    assert res3.json()["count"] == 0
