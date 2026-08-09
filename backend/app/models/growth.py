from datetime import date, datetime, timezone
from uuid import uuid4

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def new_id() -> str:
    return str(uuid4())


def now() -> datetime:
    return datetime.now(timezone.utc)


class Material(Base):
    __tablename__ = "materials"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    material_type: Mapped[str] = mapped_column(String(40), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(120), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    parse_status: Mapped[str] = mapped_column(String(40), nullable=False, default="uploaded")
    parsed_content: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    confirmation_status: Mapped[str] = mapped_column(String(40), nullable=False, default="pending_confirmation")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now, nullable=False)


class GrowthEvidence(Base):
    __tablename__ = "growth_evidences"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    material_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("materials.id", ondelete="CASCADE"), nullable=True)
    source_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    evidence_type: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    verification_status: Mapped[str] = mapped_column(String(40), nullable=False, default="pending")
    occurred_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now, nullable=False)
    __table_args__ = (UniqueConstraint("material_id", "source_key", name="uq_growth_evidence_material_source"),)


class GrowthAttribute(Base):
    __tablename__ = "growth_attributes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    attribute_key: Mapped[str] = mapped_column(String(60), nullable=False)
    current_status: Mapped[str] = mapped_column(String(40), nullable=False, default="insufficient_evidence")
    range_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    range_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    gap_status: Mapped[str] = mapped_column(String(40), nullable=False, default="unknown")
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now, nullable=False)
    __table_args__ = (UniqueConstraint("user_id", "attribute_key", name="uq_growth_attribute_user_key"),)


class AttributeEvidenceLink(Base):
    __tablename__ = "attribute_evidence_links"
    attribute_id: Mapped[str] = mapped_column(String(36), ForeignKey("growth_attributes.id", ondelete="CASCADE"), primary_key=True)
    evidence_id: Mapped[str] = mapped_column(String(36), ForeignKey("growth_evidences.id", ondelete="CASCADE"), primary_key=True)


class GoalRequirement(Base):
    __tablename__ = "goal_requirements"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    goal_id: Mapped[str] = mapped_column(String(36), ForeignKey("study_goals.id", ondelete="CASCADE"), nullable=False)
    category: Mapped[str] = mapped_column(String(60), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metric_type: Mapped[str] = mapped_column(String(40), nullable=False)
    target_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(40), nullable=True)
    importance: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    applicable_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(40), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now, nullable=False)


class WeeklyPlan(Base):
    __tablename__ = "weekly_plans"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    goal_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("study_goals.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    regeneration_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class WeeklyPlanItem(Base):
    __tablename__ = "weekly_plan_items"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    plan_id: Mapped[str] = mapped_column(String(36), ForeignKey("weekly_plans.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    task_type: Mapped[str] = mapped_column(String(40), nullable=False)
    estimated_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completion_standard: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_requirements: Mapped[str] = mapped_column(Text, nullable=False)
    generation_reason: Mapped[str] = mapped_column(Text, nullable=False)
    source_key: Mapped[str] = mapped_column(String(160), nullable=False)
    accepted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    task_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)


class EvidencePresentation(Base):
    __tablename__ = "evidence_presentations"
    evidence_id: Mapped[str] = mapped_column(String(36), ForeignKey("growth_evidences.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    user_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    hidden_from_current_goal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now, nullable=False)


class TaskOutcomeLink(Base):
    __tablename__ = "task_outcome_links"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    evaluation_id: Mapped[str] = mapped_column(String(36), ForeignKey("task_evaluations.id", ondelete="CASCADE"), nullable=False)
    growth_evidence_id: Mapped[str] = mapped_column(String(36), ForeignKey("growth_evidences.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)
    __table_args__ = (UniqueConstraint("task_id", "evaluation_id", name="uq_task_outcome_evaluation"),)


class AttributeChangeLog(Base):
    __tablename__ = "attribute_change_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    attribute_id: Mapped[str] = mapped_column(String(36), ForeignKey("growth_attributes.id", ondelete="CASCADE"), nullable=False)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    previous_status: Mapped[str] = mapped_column(String(40), nullable=False)
    new_status: Mapped[str] = mapped_column(String(40), nullable=False)
    previous_score_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    previous_score_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    new_score_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    new_score_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    previous_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    new_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)


class WeeklyReview(Base):
    __tablename__ = "weekly_reviews"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    goal_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("study_goals.id", ondelete="SET NULL"), nullable=True)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    effective_study_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pause_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_task_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    effective_task_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    partial_task_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    delayed_abandoned_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    new_item_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    progress_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    summary_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)
    __table_args__ = (UniqueConstraint("user_id", "period_start", "period_end", name="uq_weekly_review_period"),)


class PathAdjustment(Base):
    __tablename__ = "path_adjustments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    weekly_review_id: Mapped[str] = mapped_column(String(36), ForeignKey("weekly_reviews.id", ondelete="CASCADE"), nullable=False)
    adjustment_type: Mapped[str] = mapped_column(String(40), nullable=False)
    target_task_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False)
    impact: Mapped[str] = mapped_column(Text, nullable=False)
    requires_user_confirmation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
