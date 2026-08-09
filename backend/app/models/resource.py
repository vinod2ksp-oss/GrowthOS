from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def new_id() -> str:
    return str(uuid4())


def now() -> datetime:
    return datetime.now(timezone.utc)


class ResourceProduct(Base):
    __tablename__ = "resource_products"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    product_type: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    provider_name: Mapped[str | None] = mapped_column(String(255))
    cover_url: Mapped[str | None] = mapped_column(String(500))
    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    original_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(10), default="CNY", nullable=False)
    is_free: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    external_url: Mapped[str | None] = mapped_column(String(1000))
    applicable_stages: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    content_year: Mapped[int | None] = mapped_column(Integer)
    estimated_usage_days: Mapped[int | None] = mapped_column(Integer)
    difficulty_level: Mapped[str | None] = mapped_column(String(40))
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_free_alternative: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_sponsored: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sponsorship_label: Mapped[str | None] = mapped_column(String(120))
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    copyright_status: Mapped[str] = mapped_column(String(40), default="unknown", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now, nullable=False)


class ResourceAttributeLink(Base):
    __tablename__ = "resource_attribute_links"
    resource_id: Mapped[str] = mapped_column(String(36), ForeignKey("resource_products.id", ondelete="CASCADE"), primary_key=True)
    attribute_key: Mapped[str] = mapped_column(String(60), primary_key=True)


class ResourceGoalTypeLink(Base):
    __tablename__ = "resource_goal_type_links"
    resource_id: Mapped[str] = mapped_column(String(36), ForeignKey("resource_products.id", ondelete="CASCADE"), primary_key=True)
    goal_type: Mapped[str] = mapped_column(String(120), primary_key=True)


class ResourceTaskTag(Base):
    __tablename__ = "resource_task_tags"
    resource_id: Mapped[str] = mapped_column(String(36), ForeignKey("resource_products.id", ondelete="CASCADE"), primary_key=True)
    tag: Mapped[str] = mapped_column(String(120), primary_key=True)


class ResourceAlternativeLink(Base):
    __tablename__ = "resource_alternative_links"
    resource_id: Mapped[str] = mapped_column(String(36), ForeignKey("resource_products.id", ondelete="CASCADE"), primary_key=True)
    alternative_id: Mapped[str] = mapped_column(String(36), ForeignKey("resource_products.id", ondelete="CASCADE"), primary_key=True)


class UserOwnedResource(Base):
    __tablename__ = "user_owned_resources"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    resource_product_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("resource_products.id", ondelete="SET NULL"))
    custom_name: Mapped[str | None] = mapped_column(String(255))
    resource_type: Mapped[str] = mapped_column(String(40), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    acquired_at: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), default="owned", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)
    __table_args__ = (UniqueConstraint("user_id", "resource_product_id", name="uq_owned_user_product"),)


class ResourceFavorite(Base):
    __tablename__ = "resource_favorites"
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    resource_id: Mapped[str] = mapped_column(String(36), ForeignKey("resource_products.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)


class ResourceInteraction(Base):
    __tablename__ = "resource_interactions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(36), ForeignKey("resource_products.id", ondelete="CASCADE"), nullable=False)
    interaction_type: Mapped[str] = mapped_column(String(40), nullable=False)
    task_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("tasks.id", ondelete="SET NULL"))
    task_completed_at_interaction: Mapped[bool | None] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)
