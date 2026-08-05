from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import String, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class StudyGoal(Base):
    __tablename__ = "study_goals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    target_school: Mapped[str | None] = mapped_column(String(160), nullable=True)
    target_college: Mapped[str | None] = mapped_column(String(160), nullable=True)
    target_major: Mapped[str | None] = mapped_column(String(160), nullable=True)
    target_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weekly_time: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_stage: Mapped[str | None] = mapped_column(String(80), nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="study_goals")
