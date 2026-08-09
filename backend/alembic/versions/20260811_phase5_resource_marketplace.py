"""phase 5 resource marketplace

Revision ID: 20260811
Revises: 20260810
"""
from alembic import op
import sqlalchemy as sa

revision = "20260811"
down_revision = "20260810"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("role", sa.String(20), nullable=False, server_default="user"))
    op.add_column("user_profiles", sa.Column("resource_budget", sa.Float(), nullable=True))
    op.create_table("resource_products",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("name", sa.String(255), nullable=False),
        sa.Column("product_type", sa.String(40), nullable=False), sa.Column("description", sa.Text()),
        sa.Column("provider_name", sa.String(255)), sa.Column("cover_url", sa.String(500)),
        sa.Column("price", sa.Numeric(12, 2)), sa.Column("original_price", sa.Numeric(12, 2)),
        sa.Column("currency", sa.String(10), nullable=False), sa.Column("is_free", sa.Boolean(), nullable=False),
        sa.Column("external_url", sa.String(1000)), sa.Column("applicable_stages", sa.JSON(), nullable=False),
        sa.Column("content_year", sa.Integer()), sa.Column("estimated_usage_days", sa.Integer()),
        sa.Column("difficulty_level", sa.String(40)), sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("has_free_alternative", sa.Boolean(), nullable=False), sa.Column("is_sponsored", sa.Boolean(), nullable=False),
        sa.Column("sponsorship_label", sa.String(120)), sa.Column("source_type", sa.String(40), nullable=False),
        sa.Column("copyright_status", sa.String(40), nullable=False), sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("resource_attribute_links", sa.Column("resource_id", sa.String(36), sa.ForeignKey("resource_products.id", ondelete="CASCADE"), primary_key=True), sa.Column("attribute_key", sa.String(60), primary_key=True))
    op.create_table("resource_goal_type_links", sa.Column("resource_id", sa.String(36), sa.ForeignKey("resource_products.id", ondelete="CASCADE"), primary_key=True), sa.Column("goal_type", sa.String(120), primary_key=True))
    op.create_table("resource_task_tags", sa.Column("resource_id", sa.String(36), sa.ForeignKey("resource_products.id", ondelete="CASCADE"), primary_key=True), sa.Column("tag", sa.String(120), primary_key=True))
    op.create_table("resource_alternative_links", sa.Column("resource_id", sa.String(36), sa.ForeignKey("resource_products.id", ondelete="CASCADE"), primary_key=True), sa.Column("alternative_id", sa.String(36), sa.ForeignKey("resource_products.id", ondelete="CASCADE"), primary_key=True))
    op.create_table("user_owned_resources", sa.Column("id", sa.String(36), primary_key=True), sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("resource_product_id", sa.String(36), sa.ForeignKey("resource_products.id", ondelete="SET NULL")), sa.Column("custom_name", sa.String(255)), sa.Column("resource_type", sa.String(40), nullable=False), sa.Column("notes", sa.Text()), sa.Column("acquired_at", sa.Date()), sa.Column("status", sa.String(30), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("user_id", "resource_product_id", name="uq_owned_user_product"))
    op.create_table("resource_favorites", sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True), sa.Column("resource_id", sa.String(36), sa.ForeignKey("resource_products.id", ondelete="CASCADE"), primary_key=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("resource_interactions", sa.Column("id", sa.String(36), primary_key=True), sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("resource_id", sa.String(36), sa.ForeignKey("resource_products.id", ondelete="CASCADE"), nullable=False), sa.Column("interaction_type", sa.String(40), nullable=False), sa.Column("task_id", sa.String(36), sa.ForeignKey("tasks.id", ondelete="SET NULL")), sa.Column("task_completed_at_interaction", sa.Boolean()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))


def downgrade():
    for table in ["resource_interactions", "resource_favorites", "user_owned_resources", "resource_alternative_links", "resource_task_tags", "resource_goal_type_links", "resource_attribute_links", "resource_products"]:
        op.drop_table(table)
    op.drop_column("user_profiles", "resource_budget")
    op.drop_column("users", "role")
