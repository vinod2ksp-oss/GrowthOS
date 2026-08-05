from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import String, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    nickname: Mapped[str | None] = mapped_column(String(120), nullable=True)
    learning_stage: Mapped[str | None] = mapped_column(String(80), nullable=True)
    grade_level: Mapped[str | None] = mapped_column(String(80), nullable=True)
    school: Mapped[str | None] = mapped_column(String(160), nullable=True)
    major: Mapped[str | None] = mapped_column(String(160), nullable=True)
    auxiliary_direction: Mapped[str | None] = mapped_column(String(160), nullable=True)
    weekly_study_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    display_mode: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="profile")
