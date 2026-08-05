from fastapi import HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import AuthLogin, AuthRegister, UserRead


def register_user(db: Session, payload: AuthRegister) -> UserRead:
    existing = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="邮箱已注册")
    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserRead.model_validate(user)


def login_user(db: Session, payload: AuthLogin) -> dict[str, str]:
    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    token = create_access_token(subject=user.id)
    return {"access_token": token, "token_type": "bearer"}


def fetch_current_user(db: Session, token: str) -> UserRead:
    try:
        user_id = decode_access_token(token)
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="登录状态已失效") from exc
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return UserRead.model_validate(user)
