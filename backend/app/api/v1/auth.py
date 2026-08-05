from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.schemas.auth import AuthLogin, AuthRegister, TokenResponse, UserRead
from app.services.user_service import register_user, fetch_current_user, login_user

router = APIRouter(tags=["auth"])
security = HTTPBearer()


@router.post("/register", response_model=UserRead)
def register(payload: AuthRegister, db: Session = Depends(get_db)) -> UserRead:
    return register_user(db, payload)


@router.post("/login", response_model=TokenResponse)
def login(payload: AuthLogin, db: Session = Depends(get_db)) -> TokenResponse:
    return login_user(db, payload)


@router.get("/me", response_model=UserRead)
def me(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> UserRead:
    token = credentials.credentials
    return fetch_current_user(db, token)


@router.post("/logout")
def logout() -> dict[str, str]:
    return {"message": "logout completed"}
