from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

from app.schemas.growth import ATTRIBUTE_KEYS

ProductType = Literal["free_resource", "digital_material", "physical_book", "recorded_course", "live_course", "assessment", "tutoring_service", "ai_service", "other"]
ProductStatus = Literal["draft", "active", "inactive", "outdated", "rejected"]
CopyrightStatus = Literal["verified", "provider_owned", "licensed", "public", "pending", "unknown"]


class ResourceInput(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    product_type: ProductType
    description: str | None = None
    provider_name: str | None = Field(default=None, max_length=255)
    cover_url: HttpUrl | None = None
    price: float | None = Field(default=None, ge=0)
    original_price: float | None = Field(default=None, ge=0)
    currency: str = Field(default="CNY", max_length=10)
    is_free: bool = False
    external_url: HttpUrl | None = None
    applicable_stages: list[str] = Field(default_factory=list)
    related_attributes: list[ATTRIBUTE_KEYS] = Field(default_factory=list)
    related_task_tags: list[str] = Field(default_factory=list)
    applicable_goal_types: list[str] = Field(default_factory=list)
    free_alternative_ids: list[str] = Field(default_factory=list)
    content_year: int | None = Field(default=None, ge=2000, le=2200)
    estimated_usage_days: int | None = Field(default=None, ge=1)
    difficulty_level: str | None = Field(default=None, max_length=40)
    is_required: bool = False
    is_sponsored: bool = False
    sponsorship_label: str | None = Field(default=None, max_length=120)
    source_type: Literal["provider", "official", "public", "admin_entry"]
    copyright_status: CopyrightStatus = "unknown"
    status: ProductStatus = "draft"


class ResourceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    provider_name: str | None = None
    cover_url: HttpUrl | None = None
    price: float | None = Field(default=None, ge=0)
    original_price: float | None = Field(default=None, ge=0)
    external_url: HttpUrl | None = None
    applicable_stages: list[str] | None = None
    related_attributes: list[ATTRIBUTE_KEYS] | None = None
    related_task_tags: list[str] | None = None
    applicable_goal_types: list[str] | None = None
    free_alternative_ids: list[str] | None = None
    content_year: int | None = None
    estimated_usage_days: int | None = None
    difficulty_level: str | None = None
    is_required: bool | None = None
    is_sponsored: bool | None = None
    sponsorship_label: str | None = None
    copyright_status: CopyrightStatus | None = None
    status: ProductStatus | None = None


class OwnedResourceInput(BaseModel):
    resource_product_id: str | None = None
    custom_name: str | None = Field(default=None, max_length=255)
    resource_type: str = Field(min_length=1, max_length=40)
    notes: str | None = None
    acquired_at: date | None = None
    status: str = Field(default="owned", max_length=30)


class InteractionInput(BaseModel):
    interaction_type: Literal["viewed", "favorited", "external_clicked", "marked_owned", "dismissed", "used_for_task"]
    task_id: str | None = None


class AIRecommendationResult(BaseModel):
    reasons: dict[str, str]
