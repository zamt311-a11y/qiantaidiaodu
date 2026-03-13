from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import engine
from app.models.route_plan import RoutePlan
from app.models.sector import Sector
from app.models.task import Task
from app.models.task_photo import TaskPhoto
from app.models.user import User


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def bootstrap_admin(db: Session, phone: str, password: str, name: str) -> User:
    user = db.scalar(select(User).where(User.phone == phone))
    if user is not None:
        return user
    user = User(phone=phone, name=name, role="admin", password_hash=hash_password(password), is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

