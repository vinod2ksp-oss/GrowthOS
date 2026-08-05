from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.profile import UserProfile
from app.schemas.profile import ProfileCreate, ProfileRead


def upsert_profile(db: Session, user_id: str, payload: ProfileCreate) -> ProfileRead:
    profile = db.execute(select(UserProfile).where(UserProfile.user_id == user_id)).scalar_one_or_none()
    if profile is None:
        profile = UserProfile(user_id=user_id)
        db.add(profile)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return ProfileRead.model_validate(profile)


def get_profile(db: Session, user_id: str) -> ProfileRead | None:
    profile = db.execute(select(UserProfile).where(UserProfile.user_id == user_id)).scalar_one_or_none()
    if profile is None:
        return None
    return ProfileRead.model_validate(profile)
