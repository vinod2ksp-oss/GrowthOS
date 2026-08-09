from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.growth import PathAdjustment, WeeklyReview
from app.models.task import Task


class GrowthPathAdjustmentService:
    def preview(self, db: Session, user_id: str, review_id: str) -> list[PathAdjustment]:
        review = db.execute(select(WeeklyReview).where(WeeklyReview.id == review_id, WeeklyReview.user_id == user_id)).scalar_one_or_none()
        if review is None: raise LookupError("周结算不存在")
        existing = db.execute(select(PathAdjustment).where(PathAdjustment.weekly_review_id == review_id, PathAdjustment.user_id == user_id)).scalars().all()
        if existing: return existing
        tasks = db.execute(select(Task).where(Task.user_id == user_id, Task.status.in_(["pending", "delayed"]))).scalars().all()
        suggestions = []
        if review.delayed_abandoned_count and tasks:
            task = tasks[0]
            suggestions.append(PathAdjustment(user_id=user_id, weekly_review_id=review.id, adjustment_type="reduce_scope", target_task_id=task.id, reason="本周期存在延期任务，建议降低单项规模而非惩罚性降级。", recommended_action="将预计时长保守降低并保留原完成标准。", impact="降低下周负荷，任务仍需用户确认。"))
        if review.progress_json.get("missing_information"):
            suggestions.append(PathAdjustment(user_id=user_id, weekly_review_id=review.id, adjustment_type="add_information_task", reason="主线进度仍缺少必要信息。", recommended_action="下周优先补充未确认要求或能力证据。", impact="提高后续分析可信度。"))
        if not suggestions:
            suggestions.append(PathAdjustment(user_id=user_id, weekly_review_id=review.id, adjustment_type="continue", reason="当前没有证据支持大幅调整。", recommended_action="继续当前任务并保持已确认时间预算。", impact="正式任务保持不变。"))
        db.add_all(suggestions); db.commit()
        return db.execute(select(PathAdjustment).where(PathAdjustment.weekly_review_id == review_id)).scalars().all()

    def confirm(self, db: Session, user_id: str, adjustment_id: str) -> PathAdjustment:
        row = db.execute(select(PathAdjustment).where(PathAdjustment.id == adjustment_id, PathAdjustment.user_id == user_id)).scalar_one_or_none()
        if row is None: raise LookupError("调整建议不存在")
        if row.status == "confirmed": return row
        if row.target_task_id:
            task = db.execute(select(Task).where(Task.id == row.target_task_id, Task.user_id == user_id)).scalar_one_or_none()
            if task and row.adjustment_type == "reduce_scope" and task.estimated_minutes:
                task.estimated_minutes = max(15, int(task.estimated_minutes * .75))
            elif task and row.adjustment_type == "delay":
                task.deadline = (task.deadline or datetime.now(timezone.utc)) + timedelta(days=7)
        row.status = "confirmed"; row.confirmed_at = datetime.now(timezone.utc); db.commit(); db.refresh(row); return row
