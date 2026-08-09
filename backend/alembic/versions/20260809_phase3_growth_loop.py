"""phase 3 growth loop

Revision ID: 20260809
Revises: 20260805
"""
from alembic import op
import sqlalchemy as sa

revision = "20260809"
down_revision = "20260805"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("weekly_plans", sa.Column("regeneration_count", sa.Integer(), nullable=False, server_default="0"))
    op.create_table("evidence_presentations", sa.Column("evidence_id", sa.String(36), sa.ForeignKey("growth_evidences.id", ondelete="CASCADE"), primary_key=True), sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False), sa.Column("user_note", sa.Text()), sa.Column("hidden_from_current_goal", sa.Boolean(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("task_outcome_links", sa.Column("id", sa.String(36), primary_key=True), sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False), sa.Column("task_id", sa.String(36), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False), sa.Column("evaluation_id", sa.String(36), sa.ForeignKey("task_evaluations.id", ondelete="CASCADE"), nullable=False), sa.Column("growth_evidence_id", sa.String(36), sa.ForeignKey("growth_evidences.id", ondelete="CASCADE"), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("task_id", "evaluation_id", name="uq_task_outcome_evaluation"))
    op.create_table("attribute_change_logs", sa.Column("id", sa.String(36), primary_key=True), sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False), sa.Column("attribute_id", sa.String(36), sa.ForeignKey("growth_attributes.id", ondelete="CASCADE"), nullable=False), sa.Column("source_type", sa.String(40), nullable=False), sa.Column("source_id", sa.String(36)), sa.Column("previous_status", sa.String(40), nullable=False), sa.Column("new_status", sa.String(40), nullable=False), sa.Column("previous_score_min", sa.Float()), sa.Column("previous_score_max", sa.Float()), sa.Column("new_score_min", sa.Float()), sa.Column("new_score_max", sa.Float()), sa.Column("previous_confidence", sa.Float(), nullable=False), sa.Column("new_confidence", sa.Float(), nullable=False), sa.Column("reason", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("weekly_reviews", sa.Column("id", sa.String(36), primary_key=True), sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False), sa.Column("goal_id", sa.String(36), sa.ForeignKey("study_goals.id", ondelete="SET NULL")), sa.Column("period_start", sa.Date(), nullable=False), sa.Column("period_end", sa.Date(), nullable=False), sa.Column("effective_study_seconds", sa.Integer(), nullable=False), sa.Column("pause_seconds", sa.Integer(), nullable=False), sa.Column("completed_task_count", sa.Integer(), nullable=False), sa.Column("effective_task_count", sa.Integer(), nullable=False), sa.Column("partial_task_count", sa.Integer(), nullable=False), sa.Column("delayed_abandoned_count", sa.Integer(), nullable=False), sa.Column("new_item_count", sa.Integer(), nullable=False), sa.Column("progress_json", sa.JSON(), nullable=False), sa.Column("summary_json", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("user_id", "period_start", "period_end", name="uq_weekly_review_period"))
    op.create_table("path_adjustments", sa.Column("id", sa.String(36), primary_key=True), sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False), sa.Column("weekly_review_id", sa.String(36), sa.ForeignKey("weekly_reviews.id", ondelete="CASCADE"), nullable=False), sa.Column("adjustment_type", sa.String(40), nullable=False), sa.Column("target_task_id", sa.String(36), sa.ForeignKey("tasks.id", ondelete="SET NULL")), sa.Column("reason", sa.Text(), nullable=False), sa.Column("recommended_action", sa.Text(), nullable=False), sa.Column("impact", sa.Text(), nullable=False), sa.Column("requires_user_confirmation", sa.Boolean(), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("confirmed_at", sa.DateTime(timezone=True)))


def downgrade() -> None:
    for table in ["path_adjustments", "weekly_reviews", "attribute_change_logs", "task_outcome_links", "evidence_presentations"]:
        op.drop_table(table)
    op.drop_column("weekly_plans", "regeneration_count")
