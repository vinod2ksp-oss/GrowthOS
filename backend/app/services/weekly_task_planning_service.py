from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.goal import StudyGoal
from app.models.growth import GoalRequirement, WeeklyPlan, WeeklyPlanItem
from app.models.profile import UserProfile
from app.models.task import Task
from app.services.goal_gap_analysis_service import GoalGapAnalysisService


class WeeklyTaskPlanningService:
    def generate(self, db: Session, user_id: str, goal_id: str | None, review_id: str | None = None) -> WeeklyPlan:
        profile = db.execute(select(UserProfile).where(UserProfile.user_id == user_id)).scalar_one_or_none()
        budget = max(30, (profile.weekly_study_hours or 1) * 60)
        existing_titles = set(db.execute(select(Task.title).where(Task.user_id == user_id)).scalars().all())
        existing_source_keys = set(db.execute(select(WeeklyPlanItem.source_key).join(WeeklyPlan, WeeklyPlan.id == WeeklyPlanItem.plan_id).where(WeeklyPlan.user_id == user_id, WeeklyPlan.status == "draft")).scalars().all())
        plan = WeeklyPlan(user_id=user_id, goal_id=goal_id)
        db.add(plan); db.flush()
        candidates: list[dict] = []
        requirements = []
        gaps = []
        if goal_id:
            goal = db.execute(select(StudyGoal).where(StudyGoal.id == goal_id, StudyGoal.user_id == user_id)).scalar_one_or_none()
            if goal is None: raise LookupError("目标不存在")
            requirements = db.execute(select(GoalRequirement).where(GoalRequirement.goal_id == goal_id, GoalRequirement.verification_status == "confirmed")).scalars().all()
            gaps = GoalGapAnalysisService().analyze(db, user_id, goal_id)
        if not requirements:
            candidates.append(self._candidate("补充并确认目标要求", "main", min(60, budget), "至少录入并确认一项目标要求。", "目标要求记录", "当前没有已确认的目标要求，先补全信息。", "missing-requirements"))
        else:
            for index, gap in enumerate([g for g in gaps if g["gap_level"] != "no_gap"][:3]):
                task_type = "main" if index == 0 else "support"
                title = f"补充 {gap['title']} 的能力证据" if gap["gap_level"] == "unknown" else f"推进 {gap['title']}"
                candidates.append(self._candidate(title, task_type, min(120, budget), "完成一次可核验的学习或信息补全过程。", "上传结果或更新确认信息", f"差距分析为 {gap['gap_level']}：{gap['next_step']}", f"requirement:{gap['requirement_id']}"))
        if review_id:
            unfinished = db.execute(select(Task).where(Task.user_id == user_id, Task.status.in_(["pending", "delayed"])).order_by(Task.created_at)).scalars().all()
            for task in unfinished[:2]:
                candidates.insert(0, self._candidate(f"继续：{task.title}", "support", min(task.estimated_minutes or 60, budget), task.completion_standard or "完成延续任务并更新状态。", task.evidence_requirements or "提交可核验结果", "上周任务尚未完成，保留目标并缩小为下周可执行项。", f"continue:{task.id}"))
        if profile is None or profile.weekly_study_hours is None:
            candidates.insert(0, self._candidate("确认当前每周可投入时间", "main", 30, "在个人档案中确认每周可投入小时数。", "更新后的个人档案", "缺少时间预算，无法可靠安排学习负荷。", "missing-time"))
        counts = {"main": 0, "support": 0, "challenge": 0}; used = 0
        for item in candidates:
            cap = {"main": 1, "support": 2, "challenge": 1}[item["task_type"]]
            if item["title"] in existing_titles or item["source_key"] in existing_source_keys or counts[item["task_type"]] >= cap or used + item["estimated_minutes"] > budget: continue
            db.add(WeeklyPlanItem(plan_id=plan.id, deadline=datetime.now(timezone.utc) + timedelta(days=7), **item))
            counts[item["task_type"]] += 1; used += item["estimated_minutes"]
        db.commit(); db.refresh(plan)
        return plan

    def confirm(self, db: Session, user_id: str, plan_id: str, accepted: list[str] | None) -> WeeklyPlan:
        plan = db.execute(select(WeeklyPlan).where(WeeklyPlan.id == plan_id, WeeklyPlan.user_id == user_id)).scalar_one_or_none()
        if plan is None: raise LookupError("计划不存在")
        if plan.status == "confirmed": return plan
        items = db.execute(select(WeeklyPlanItem).where(WeeklyPlanItem.plan_id == plan.id)).scalars().all()
        accepted_set = set(accepted) if accepted is not None else {item.id for item in items}
        existing = set(db.execute(select(Task.title).where(Task.user_id == user_id)).scalars().all())
        for item in items:
            item.accepted = item.id in accepted_set
            if item.accepted and item.title not in existing:
                task = Task(user_id=user_id, title=item.title, task_type=item.task_type, status="pending", deadline=item.deadline, estimated_minutes=item.estimated_minutes, completion_standard=item.completion_standard, evidence_requirements=item.evidence_requirements)
                db.add(task); db.flush(); item.task_id = task.id; existing.add(item.title)
        plan.status = "confirmed"; plan.confirmed_at = datetime.now(timezone.utc)
        db.commit(); db.refresh(plan)
        return plan

    def _candidate(self, title: str, task_type: str, minutes: int, standard: str, evidence: str, reason: str, source_key: str) -> dict:
        return {"title": title, "task_type": task_type, "estimated_minutes": minutes, "completion_standard": standard, "evidence_requirements": evidence, "generation_reason": reason, "source_key": source_key}
