from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.security import hash_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserAdminUpdate, UserCreate, UserOut


router = APIRouter()


@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
    q: str | None = None,
    role: str | None = None,
    is_active: bool | None = Query(default=None),
) -> list[UserOut]:
    stmt = select(User)
    if role:
        stmt = stmt.where(User.role == role)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(User.name.ilike(like), User.phone.ilike(like)))
    users = list(db.scalars(stmt.order_by(User.id.desc())).all())
    return [UserOut.model_validate(u) for u in users]


@router.post("", response_model=UserOut)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> UserOut:
    phone = payload.phone.strip()
    name = payload.name.strip()
    role = (payload.role or "engineer").strip() or "engineer"
    if not phone or not name or not payload.password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="手机号/姓名/密码不能为空")
    if role not in ("admin", "engineer"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="角色不合法")
    exists = db.scalar(select(User.id).where(User.phone == phone))
    if exists is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="手机号已存在")
    u = User(phone=phone, name=name, role=role, password_hash=hash_password(payload.password), is_active=True)
    db.add(u)
    db.commit()
    db.refresh(u)
    return UserOut.model_validate(u)


@router.patch("/{user_id}", response_model=UserOut)
def admin_update_user(
    user_id: int,
    payload: UserAdminUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> UserOut:
    u = db.get(User, user_id)
    if u is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    if payload.name is not None:
        v = payload.name.strip()
        if not v:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="姓名不能为空")
        u.name = v
    if payload.role is not None:
        v = payload.role.strip()
        if v not in ("admin", "engineer"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="角色不合法")
        u.role = v
    if payload.password is not None:
        if not payload.password:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="密码不能为空")
        u.password_hash = hash_password(payload.password)
    if payload.is_active is not None:
        u.is_active = bool(payload.is_active)
    db.add(u)
    db.commit()
    db.refresh(u)
    return UserOut.model_validate(u)

