from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.message import Message
from app.models.device_token import DeviceToken
from app.models.op_log import OpLog
from app.models.user import User


def _get_admin_user_id() -> int:
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.phone == "13800000000"))
        assert user is not None
        return int(user.id)


def test_device_token_create(client):
    user_id = _get_admin_user_id()
    with SessionLocal() as db:
        token = DeviceToken(user_id=user_id, token="token-1", platform="android")
        db.add(token)
        db.commit()
        assert token.id is not None


def test_message_and_op_log_create(client):
    user_id = _get_admin_user_id()
    with SessionLocal() as db:
        msg = Message(user_id=user_id, title="t", content="c", msg_type="system")
        db.add(msg)
        log = OpLog(user_id=user_id, action="test", detail="detail")
        db.add(log)
        db.commit()
        assert msg.id is not None
        assert log.id is not None
