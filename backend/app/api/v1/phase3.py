from datetime import date, datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.models.goal import StudyGoal
from app.models.growth import AttributeChangeLog, GoalRequirement, GrowthEvidence, PathAdjustment, WeeklyPlan, WeeklyPlanItem, WeeklyReview
from app.models.user import User
from app.schemas.growth import InventoryPreferenceInput, PlanItemUpdate, ReviewInput, TaskOutcomeInput
from app.services.growth_diagnosis_service import GrowthDiagnosisService
from app.services.growth_path_adjustment_service import GrowthPathAdjustmentService
from app.services.inventory_service import InventoryService
from app.services.task_outcome_service import TaskOutcomeService
from app.services.weekly_review_service import WeeklyReviewService

router = APIRouter(tags=["phase3"])


def dump(row) -> dict:
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


@router.post("/tasks/{task_id}/outcome", status_code=201)
def convert_outcome(task_id: str, payload: TaskOutcomeInput, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    try: return dump(TaskOutcomeService().convert(db, user.id, task_id, payload.outcome_type, payload.attribute_key))
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc
    except ValueError as exc: raise HTTPException(409, str(exc)) from exc


@router.get("/inventory")
def inventory(evidence_type: str | None = None, attribute_key: str | None = None, goal_id: str | None = None, relevant_only: bool = False, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    relevant_attributes = None
    if goal_id:
        goal = db.execute(select(StudyGoal).where(StudyGoal.id == goal_id, StudyGoal.user_id == user.id)).scalar_one_or_none()
        if goal is None: raise HTTPException(404, "目标不存在")
        relevant_attributes = set(db.execute(select(GoalRequirement.category).where(GoalRequirement.goal_id == goal_id, GoalRequirement.verification_status == "confirmed")).scalars().all())
    return InventoryService().list(db, user.id, evidence_type, attribute_key, relevant_only, relevant_attributes)


@router.get("/inventory/{evidence_id}")
def inventory_detail(evidence_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    rows = InventoryService().list(db, user.id)
    row = next((item for item in rows if item["id"] == evidence_id), None)
    if row is None: raise HTTPException(404, "背包物品不存在")
    return row


@router.patch("/inventory/{evidence_id}", status_code=204)
def update_inventory(evidence_id: str, payload: InventoryPreferenceInput, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    try: InventoryService().update_presentation(db, user.id, evidence_id, payload.user_note, payload.hidden_from_current_goal)
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc


@router.post("/growth-evidences/{evidence_id}/reject")
def reject_evidence(evidence_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    row = db.execute(select(GrowthEvidence).where(GrowthEvidence.id == evidence_id, GrowthEvidence.user_id == user.id)).scalar_one_or_none()
    if row is None: raise HTTPException(404, "成长证据不存在")
    row.verification_status = "rejected"; db.commit()
    GrowthDiagnosisService().diagnose(db, user.id, "evidence_rejected", row.id)
    return dump(row)


@router.get("/attribute-changes")
def attribute_changes(attribute_id: str | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    query = select(AttributeChangeLog).where(AttributeChangeLog.user_id == user.id)
    if attribute_id: query = query.where(AttributeChangeLog.attribute_id == attribute_id)
    return [dump(row) for row in db.execute(query.order_by(AttributeChangeLog.created_at.desc())).scalars().all()]


@router.post("/weekly-reviews", status_code=201)
def create_review(payload: ReviewInput, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    try: return dump(WeeklyReviewService().generate(db, user.id, payload.period_start, payload.goal_id))
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc


@router.get("/weekly-reviews")
def reviews(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    return [dump(row) for row in db.execute(select(WeeklyReview).where(WeeklyReview.user_id == user.id).order_by(WeeklyReview.period_start.desc())).scalars().all()]


@router.get("/weekly-reviews/{review_id}")
def review_detail(review_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    row = db.execute(select(WeeklyReview).where(WeeklyReview.id == review_id, WeeklyReview.user_id == user.id)).scalar_one_or_none()
    if row is None: raise HTTPException(404, "周结算不存在")
    return dump(row)


@router.post("/weekly-reviews/{review_id}/adjustments")
def preview_adjustments(review_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    try: return [dump(row) for row in GrowthPathAdjustmentService().preview(db, user.id, review_id)]
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc


@router.get("/path-adjustments")
def adjustments(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    return [dump(row) for row in db.execute(select(PathAdjustment).where(PathAdjustment.user_id == user.id).order_by(PathAdjustment.created_at.desc())).scalars().all()]


@router.post("/path-adjustments/{adjustment_id}/confirm")
def confirm_adjustment(adjustment_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    try: return dump(GrowthPathAdjustmentService().confirm(db, user.id, adjustment_id))
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc


@router.patch("/weekly-plans/{plan_id}/items/{item_id}")
def update_plan_item(plan_id: str, item_id: str, payload: PlanItemUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    plan = db.execute(select(WeeklyPlan).where(WeeklyPlan.id == plan_id, WeeklyPlan.user_id == user.id, WeeklyPlan.status == "draft")).scalar_one_or_none()
    if plan is None: raise HTTPException(404, "待确认计划不存在")
    item = db.execute(select(WeeklyPlanItem).where(WeeklyPlanItem.id == item_id, WeeklyPlanItem.plan_id == plan.id)).scalar_one_or_none()
    if item is None: raise HTTPException(404, "计划任务不存在")
    for key, value in payload.model_dump(exclude_unset=True).items(): setattr(item, key, value)
    db.commit(); db.refresh(item); return dump(item)


@router.delete("/weekly-plans/{plan_id}/items/{item_id}", status_code=204)
def delete_plan_item(plan_id: str, item_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    plan = db.execute(select(WeeklyPlan).where(WeeklyPlan.id == plan_id, WeeklyPlan.user_id == user.id, WeeklyPlan.status == "draft")).scalar_one_or_none()
    item = db.execute(select(WeeklyPlanItem).where(WeeklyPlanItem.id == item_id, WeeklyPlanItem.plan_id == plan_id)).scalar_one_or_none() if plan else None
    if item is None: raise HTTPException(404, "计划任务不存在")
    db.delete(item); db.commit()


@router.post("/weekly-plans/{plan_id}/regenerate", status_code=201)
def regenerate_plan(plan_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    from app.services.weekly_task_planning_service import WeeklyTaskPlanningService
    plan = db.execute(select(WeeklyPlan).where(WeeklyPlan.id == plan_id, WeeklyPlan.user_id == user.id, WeeklyPlan.status == "draft")).scalar_one_or_none()
    if plan is None: raise HTTPException(404, "待确认计划不存在")
    if plan.regeneration_count >= 1: raise HTTPException(409, "同一计划只允许重新生成一次")
    plan.status = "superseded"; db.flush()
    replacement = WeeklyTaskPlanningService().generate(db, user.id, plan.goal_id)
    replacement.regeneration_count = plan.regeneration_count + 1; db.commit(); db.refresh(replacement)
    return {**dump(replacement), "items": [dump(item) for item in db.execute(select(WeeklyPlanItem).where(WeeklyPlanItem.plan_id == replacement.id)).scalars().all()]}


@router.post("/weekly-plans/{plan_id}/items/{item_id}/delay")
def delay_plan_item(plan_id: str, item_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    plan = db.execute(select(WeeklyPlan).where(WeeklyPlan.id == plan_id, WeeklyPlan.user_id == user.id, WeeklyPlan.status == "draft")).scalar_one_or_none()
    item = db.execute(select(WeeklyPlanItem).where(WeeklyPlanItem.id == item_id, WeeklyPlanItem.plan_id == plan_id)).scalar_one_or_none() if plan else None
    if item is None: raise HTTPException(404, "计划任务不存在")
    item.deadline += timedelta(days=7); db.commit(); db.refresh(item); return dump(item)


@router.get("/growth-dashboard")
def growth_dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    latest_review = db.execute(select(WeeklyReview).where(WeeklyReview.user_id == user.id).order_by(WeeklyReview.period_end.desc())).scalars().first()
    recent_items = InventoryService().list(db, user.id)[:3]
    changes = db.execute(select(AttributeChangeLog).where(AttributeChangeLog.user_id == user.id).order_by(AttributeChangeLog.created_at.desc()).limit(3)).scalars().all()
    pending = db.execute(select(WeeklyPlan).where(WeeklyPlan.user_id == user.id, WeeklyPlan.status == "draft")).scalars().all()
    next_review = (latest_review.period_end + timedelta(days=7)) if latest_review else None
    return {"weekly_completion": (latest_review.effective_task_count / latest_review.completed_task_count) if latest_review and latest_review.completed_task_count else None, "recent_items": recent_items, "recent_attribute_changes": [dump(row) for row in changes], "current_risks": latest_review.summary_json.get("risks", []) if latest_review else [], "next_review_date": next_review, "pending_plan_count": len(pending), "data_source": "真实任务、学习会话、成长证据和周结算"}
