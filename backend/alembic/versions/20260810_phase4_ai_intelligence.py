"""phase 4 optional ai intelligence

Revision ID: 20260810
Revises: 20260809
"""
from alembic import op
import sqlalchemy as sa
revision="20260810"; down_revision="20260809"; branch_labels=None; depends_on=None
def upgrade():
    op.create_table("ai_user_settings",sa.Column("user_id",sa.String(36),sa.ForeignKey("users.id"),primary_key=True),sa.Column("allow_material_analysis",sa.Boolean(),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False))
    op.create_table("ai_analyses",sa.Column("id",sa.String(36),primary_key=True),sa.Column("user_id",sa.String(36),sa.ForeignKey("users.id"),nullable=False),sa.Column("analysis_type",sa.String(50),nullable=False),sa.Column("source_type",sa.String(40),nullable=False),sa.Column("source_id",sa.String(36)),sa.Column("status",sa.String(40),nullable=False),sa.Column("result_json",sa.JSON()),sa.Column("error_code",sa.String(80)),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("confirmed_at",sa.DateTime(timezone=True)))
    op.create_table("ai_call_logs",sa.Column("id",sa.String(36),primary_key=True),sa.Column("user_id",sa.String(36),sa.ForeignKey("users.id"),nullable=False),sa.Column("feature",sa.String(50),nullable=False),sa.Column("model",sa.String(120),nullable=False),sa.Column("status",sa.String(30),nullable=False),sa.Column("prompt_chars",sa.Integer(),nullable=False),sa.Column("input_tokens",sa.Integer()),sa.Column("output_tokens",sa.Integer()),sa.Column("latency_ms",sa.Integer(),nullable=False),sa.Column("error_code",sa.String(80)),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
    op.create_table("ai_followups",sa.Column("id",sa.String(36),primary_key=True),sa.Column("user_id",sa.String(36),sa.ForeignKey("users.id"),nullable=False),sa.Column("task_id",sa.String(36),sa.ForeignKey("tasks.id",ondelete="CASCADE"),nullable=False),sa.Column("question",sa.Text(),nullable=False),sa.Column("answer",sa.Text()),sa.Column("evaluation",sa.Text()),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.UniqueConstraint("task_id","question",name="uq_ai_followup_task_question"))
def downgrade():
    for table in ["ai_followups","ai_call_logs","ai_analyses","ai_user_settings"]: op.drop_table(table)
