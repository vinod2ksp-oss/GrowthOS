"""phase 2 growth profile

Revision ID: 20260805
Revises: 20260804
"""
from alembic import op
import sqlalchemy as sa

revision = "20260805"
down_revision = "20260804"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("materials", sa.Column("id", sa.String(36), primary_key=True), sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False), sa.Column("material_type", sa.String(40), nullable=False), sa.Column("original_filename", sa.String(255), nullable=False), sa.Column("stored_filename", sa.String(255), nullable=False), sa.Column("mime_type", sa.String(120), nullable=False), sa.Column("file_size", sa.Integer(), nullable=False), sa.Column("storage_path", sa.String(500), nullable=False), sa.Column("parse_status", sa.String(40), nullable=False), sa.Column("parsed_content", sa.JSON()), sa.Column("confirmation_status", sa.String(40), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_materials_user_id", "materials", ["user_id"])
    op.create_table("growth_evidences", sa.Column("id", sa.String(36), primary_key=True), sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False), sa.Column("material_id", sa.String(36), sa.ForeignKey("materials.id", ondelete="CASCADE")), sa.Column("source_key", sa.String(120)), sa.Column("evidence_type", sa.String(40), nullable=False), sa.Column("title", sa.String(255), nullable=False), sa.Column("description", sa.Text()), sa.Column("source_type", sa.String(40), nullable=False), sa.Column("verification_status", sa.String(40), nullable=False), sa.Column("occurred_at", sa.Date()), sa.Column("valid_until", sa.Date()), sa.Column("metadata_json", sa.JSON()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("material_id", "source_key", name="uq_growth_evidence_material_source"))
    op.create_index("ix_growth_evidences_user_id", "growth_evidences", ["user_id"])
    op.create_table("growth_attributes", sa.Column("id", sa.String(36), primary_key=True), sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False), sa.Column("attribute_key", sa.String(60), nullable=False), sa.Column("current_status", sa.String(40), nullable=False), sa.Column("range_min", sa.Float()), sa.Column("range_max", sa.Float()), sa.Column("confidence", sa.Float(), nullable=False), sa.Column("gap_status", sa.String(40), nullable=False), sa.Column("explanation", sa.Text(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("user_id", "attribute_key", name="uq_growth_attribute_user_key"))
    op.create_table("attribute_evidence_links", sa.Column("attribute_id", sa.String(36), sa.ForeignKey("growth_attributes.id", ondelete="CASCADE"), primary_key=True), sa.Column("evidence_id", sa.String(36), sa.ForeignKey("growth_evidences.id", ondelete="CASCADE"), primary_key=True))
    op.create_table("goal_requirements", sa.Column("id", sa.String(36), primary_key=True), sa.Column("goal_id", sa.String(36), sa.ForeignKey("study_goals.id", ondelete="CASCADE"), nullable=False), sa.Column("category", sa.String(60), nullable=False), sa.Column("title", sa.String(255), nullable=False), sa.Column("description", sa.Text()), sa.Column("metric_type", sa.String(40), nullable=False), sa.Column("target_min", sa.Float()), sa.Column("target_max", sa.Float()), sa.Column("unit", sa.String(40)), sa.Column("importance", sa.String(20), nullable=False), sa.Column("source_type", sa.String(40), nullable=False), sa.Column("source_url", sa.String(500)), sa.Column("applicable_year", sa.Integer()), sa.Column("verification_status", sa.String(40), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("weekly_plans", sa.Column("id", sa.String(36), primary_key=True), sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False), sa.Column("goal_id", sa.String(36), sa.ForeignKey("study_goals.id", ondelete="SET NULL")), sa.Column("status", sa.String(30), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("confirmed_at", sa.DateTime(timezone=True)))
    op.create_table("weekly_plan_items", sa.Column("id", sa.String(36), primary_key=True), sa.Column("plan_id", sa.String(36), sa.ForeignKey("weekly_plans.id", ondelete="CASCADE"), nullable=False), sa.Column("title", sa.String(200), nullable=False), sa.Column("task_type", sa.String(40), nullable=False), sa.Column("estimated_minutes", sa.Integer(), nullable=False), sa.Column("deadline", sa.DateTime(timezone=True), nullable=False), sa.Column("completion_standard", sa.Text(), nullable=False), sa.Column("evidence_requirements", sa.Text(), nullable=False), sa.Column("generation_reason", sa.Text(), nullable=False), sa.Column("source_key", sa.String(160), nullable=False), sa.Column("accepted", sa.Boolean(), nullable=False), sa.Column("task_id", sa.String(36), sa.ForeignKey("tasks.id", ondelete="SET NULL")))


def downgrade() -> None:
    for table in ["weekly_plan_items", "weekly_plans", "goal_requirements", "attribute_evidence_links", "growth_attributes", "growth_evidences", "materials"]:
        op.drop_table(table)
