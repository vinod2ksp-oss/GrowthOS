from datetime import date, datetime, time, timedelta, timezone
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.goal import StudyGoal
from app.models.growth import AttributeChangeLog, GoalRequirement, GrowthEvidence, TaskOutcomeLink, WeeklyReview
from app.models.profile import UserProfile
from app.models.task import LearningSession, Task, TaskEvaluation
from app.services.goal_gap_analysis_service import GoalGapAnalysisService


class WeeklyReviewService:
    def generate(self, db: Session, user_id: str, period_start: date, goal_id: str | None = None) -> WeeklyReview:
        period_end = period_start + timedelta(days=6)
        existing = db.execute(select(WeeklyReview).where(WeeklyReview.user_id == user_id, WeeklyReview.period_start == period_start, WeeklyReview.period_end == period_end)).scalar_one_or_none()
        if existing: return existing
        start_dt = datetime.combine(period_start, time.min, timezone.utc); end_dt = datetime.combine(period_end + timedelta(days=1), time.min, timezone.utc)
        tasks = db.execute(select(Task).where(Task.user_id == user_id, Task.updated_at >= start_dt, Task.updated_at < end_dt)).scalars().all()
        sessions = db.execute(select(LearningSession).where(LearningSession.user_id == user_id, LearningSession.created_at >= start_dt, LearningSession.created_at < end_dt)).scalars().all()
        evaluations = db.execute(select(TaskEvaluation).where(TaskEvaluation.user_id == user_id, TaskEvaluation.created_at >= start_dt, TaskEvaluation.created_at < end_dt)).scalars().all()
        outcomes = db.execute(select(TaskOutcomeLink).where(TaskOutcomeLink.user_id == user_id, TaskOutcomeLink.created_at >= start_dt, TaskOutcomeLink.created_at < end_dt)).scalars().all()
        changes = db.execute(select(AttributeChangeLog).where(AttributeChangeLog.user_id == user_id, AttributeChangeLog.created_at >= start_dt, AttributeChangeLog.created_at < end_dt)).scalars().all()
        effective = sum(item.elapsed_seconds for item in sessions); paused = sum(item.pause_total_seconds for item in sessions)
        completed = sum(item.status == "done" for item in tasks); valid = sum(item.status == "completed" for item in evaluations); partial = sum(item.status == "partial_complete" for item in evaluations)
        now = datetime.now(timezone.utc)
        def is_delayed(item: Task) -> bool:
            deadline = item.deadline
            if deadline and deadline.tzinfo is None: deadline = deadline.replace(tzinfo=timezone.utc)
            return item.status in {"delayed", "abandoned"} or bool(deadline and deadline < now and item.status != "done")
        delayed = sum(is_delayed(item) for item in tasks)
        progress = self.progress(db, user_id, goal_id, tasks)
        profile = db.execute(select(UserProfile).where(UserProfile.user_id == user_id)).scalar_one_or_none()
        budget_seconds = (profile.weekly_study_hours or 0) * 3600 if profile else 0
        gaps = GoalGapAnalysisService().analyze(db, user_id, goal_id) if goal_id else []
        risks = []
        if delayed: risks.append(f"存在 {delayed} 个延期或放弃任务。")
        if budget_seconds and effective > budget_seconds * 1.2: risks.append("实际投入超过已确认时间预算，需检查下周负荷。")
        unresolved = [gap["title"] for gap in gaps if gap["gap_level"] in {"unknown", "moderate", "major"}]
        summary = {"main_progress": "信息不完整" if progress["progress_value"] is None else f"{progress['progress_value']:.0%}", "major_progress": [f"新增 {len(outcomes)} 项可追溯成果"] if outcomes else [], "risks": risks, "unresolved_gaps": unresolved, "next_week_suggestions": ["优先处理延期任务"] if delayed else ["保持与当前时间预算一致的任务规模"], "attribute_change_count": len(changes), "confidence_change": sum(change.new_confidence - change.previous_confidence for change in changes), "available_minutes": budget_seconds // 60}
        prior_items = db.scalar(select(func.count(GrowthEvidence.id)).where(GrowthEvidence.user_id == user_id, GrowthEvidence.created_at >= start_dt, GrowthEvidence.created_at < end_dt)) or 0
        review = WeeklyReview(user_id=user_id, goal_id=goal_id, period_start=period_start, period_end=period_end, effective_study_seconds=effective, pause_seconds=paused, completed_task_count=completed, effective_task_count=valid, partial_task_count=partial, delayed_abandoned_count=delayed, new_item_count=prior_items + 1, progress_json=progress, summary_json=summary)
        db.add(review); db.flush()
        db.add(GrowthEvidence(user_id=user_id, source_key=f"weekly-review:{period_start.isoformat()}", evidence_type="other", title=f"周度阶段报告 {period_start.isoformat()} 至 {period_end.isoformat()}", description="由真实任务、评测、学习会话、证据与属性变化汇总生成。", source_type="system_report", verification_status="system_verified", metadata_json={"weekly_review_id": review.id, "period_start": period_start.isoformat(), "period_end": period_end.isoformat()}))
        db.commit(); db.refresh(review); return review

    def progress(self, db: Session, user_id: str, goal_id: str | None, tasks: list[Task]) -> dict:
        if not goal_id: return {"progress_value": None, "confidence": 0, "explanation": "未选择目标，无法计算主线进度。", "missing_information": ["目标"]}
        goal = db.execute(select(StudyGoal).where(StudyGoal.id == goal_id, StudyGoal.user_id == user_id)).scalar_one_or_none()
        if goal is None: raise LookupError("目标不存在")
        requirements = db.execute(select(GoalRequirement).where(GoalRequirement.goal_id == goal_id, GoalRequirement.verification_status == "confirmed")).scalars().all()
        if not requirements: return {"progress_value": None, "confidence": 0, "explanation": "没有已确认目标要求，不能生成百分比。", "missing_information": ["已确认目标要求"]}
        gaps = GoalGapAnalysisService().analyze(db, user_id, goal_id)
        evidence_covered = sum(bool(gap["current_evidence"]) for gap in gaps) / len(requirements)
        no_gap = sum(gap["gap_level"] == "no_gap" for gap in gaps) / len(requirements)
        relevant_tasks = [task for task in tasks if task.status in {"pending", "done", "delayed", "abandoned"}]
        task_completion = sum(task.status == "done" for task in relevant_tasks) / len(relevant_tasks) if relevant_tasks else 0
        value = .4 * evidence_covered + .35 * no_gap + .25 * task_completion
        confidence = min(1.0, .4 + .1 * len(requirements) + .2 * evidence_covered)
        return {"progress_value": value, "confidence": confidence, "explanation": "由已确认要求的证据覆盖度、核心差距状态和当前任务完成情况加权计算，不按任务数量直接平均。", "missing_information": [gap["title"] for gap in gaps if gap["gap_level"] == "unknown"]}
