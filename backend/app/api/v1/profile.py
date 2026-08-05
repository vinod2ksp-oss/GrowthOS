from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.profile import ProfileCreate, ProfileRead
from app.services.profile_service import get_profile, upsert_profile

router = APIRouter(tags=["profile"])


@router.get("/profile", response_model=ProfileRead | None)
def read_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ProfileRead | None:
    return get_profile(db, current_user.id)


@router.put("/profile", response_model=ProfileRead)
def write_profile(payload: ProfileCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ProfileRead:
    return upsert_profile(db, current_user.id, payload)
