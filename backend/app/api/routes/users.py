from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.security import hash_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserAdminUpdate, UserCreate, UserOut


router = APIRouter()


def _can_manage(current: User, target: User) -> bool:
    if current.role == "super_admin":
        return True
    return current.role == "admin" and target.role == "engineer"


def _can_create_role(current: User, role: str) -> bool:
    if current.role == "super_admin":
        return role in ("admin", "engineer")
    if current.role == "admin":
        return role == "engineer"
    return False


def _is_valid_role(role: str) -> bool:
    return role in ("admin", "engineer", "super_admin")


@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    q: str | None = None,
    role: str | None = None,
    is_active: bool | None = Query(default=None),
) -> list[UserOut]:
    stmt = select(User)
    if current_user.role == "admin":
        stmt = stmt.where(User.role == "engineer")
    elif role:
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
    current_user: User = Depends(require_admin),
) -> UserOut:
    phone = payload.phone.strip()
    name = payload.name.strip()
    role = (payload.role or "engineer").strip() or "engineer"
    if not phone or not name or not payload.password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="手机号/姓名/密码不能为空")
    if not _is_valid_role(role):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="角色不合法")
    if role == "super_admin":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="涓嶆敮鎸佸垱寤轿绾(super_admin)")
    if not _can_create_role(current_user, role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="鏃犳潈闄?")
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
    current_user: User = Depends(require_admin),
) -> UserOut:
    u = db.get(User, user_id)
    if u is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    if not _can_manage(current_user, u):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="鏃犳潈闄?")
    if payload.name is not None:
        v = payload.name.strip()
        if not v:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="姓名不能为空")
        u.name = v
    if payload.role is not None:
        v = payload.role.strip()
        if not _is_valid_role(v) or v == "super_admin":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="角色不合法")
        if current_user.role == "admin" and v != "engineer":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="鏃犳潈闄?")
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


@router.post("/{user_id}/reset_password")
def reset_password(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    u = db.get(User, user_id)
    if u is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="鐢ㄦ埛涓嶅瓨鍦?")
    if not _can_manage(current_user, u):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="鏃犳潈闄?")
    new_pwd = secrets.token_urlsafe(8)
    u.password_hash = hash_password(new_pwd)
    db.add(u)
    db.commit()
    return {"password": new_pwd}


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    u = db.get(User, user_id)
    if u is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="鐢ㄦ埛涓嶅瓨鍦?")
    if u.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="涓嶈兘鍒犻櫎鑷繁")
    if not _can_manage(current_user, u):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="鏃犳潈闄?")
    u.is_active = False
    db.add(u)
    db.commit()
    return {"deleted": 1}

