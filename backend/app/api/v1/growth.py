from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.models.goal import StudyGoal
from app.models.growth import GoalRequirement, GrowthEvidence, Material, WeeklyPlanItem
from app.models.user import User
from app.schemas.growth import MaterialConfirmation, PlanConfirmation, RequirementInput, RequirementUpdate
from app.services.goal_gap_analysis_service import GoalGapAnalysisService
from app.services.growth_diagnosis_service import GrowthDiagnosisService
from app.services.material_service import MaterialService
from app.services.weekly_task_planning_service import WeeklyTaskPlanningService

router = APIRouter(tags=["growth"])


def dump(row) -> dict:
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


@router.post("/materials", status_code=201)
def upload_material(material_type: str = Form(...), file: UploadFile = File(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    try: return dump(MaterialService().upload(db, user.id, material_type, file))
    except ValueError as exc: raise HTTPException(400, str(exc)) from exc


@router.get("/materials")
def list_materials(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    return [dump(row) for row in db.execute(select(Material).where(Material.user_id == user.id).order_by(Material.created_at.desc())).scalars().all()]


@router.get("/materials/{material_id}")
def get_material(material_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    row = db.execute(select(Material).where(Material.id == material_id, Material.user_id == user.id)).scalar_one_or_none()
    if row is None: raise HTTPException(404, "材料不存在")
    return dump(row)


@router.post("/materials/{material_id}/confirm")
def confirm_material(material_id: str, payload: MaterialConfirmation, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    try: return [dump(row) for row in MaterialService().confirm(db, user.id, material_id, payload)]
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc


@router.delete("/materials/{material_id}", status_code=204)
def delete_material(material_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    try: MaterialService().delete(db, user.id, material_id)
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc


@router.get("/growth-evidences")
def evidences(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    return [dump(row) for row in db.execute(select(GrowthEvidence).where(GrowthEvidence.user_id == user.id).order_by(GrowthEvidence.created_at.desc())).scalars().all()]


@router.get("/growth-attributes")
def attributes(goal_id: str | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    values = GrowthDiagnosisService().diagnose(db, user.id)
    if not goal_id:
        return [{**value, "target_range": None} for value in values]
    owned_goal(db, user.id, goal_id)
    gaps = GoalGapAnalysisService().analyze(db, user.id, goal_id)
    by_category = {gap["category"]: gap for gap in gaps}
    return [{**value, "target_range": by_category.get(value["attribute_key"], {}).get("target"), "gap_status": by_category.get(value["attribute_key"], {}).get("gap_level", "unknown")} for value in values]


def owned_goal(db: Session, user_id: str, goal_id: str) -> StudyGoal:
    goal = db.execute(select(StudyGoal).where(StudyGoal.id == goal_id, StudyGoal.user_id == user_id)).scalar_one_or_none()
    if goal is None: raise HTTPException(404, "目标不存在")
    return goal


@router.get("/goals/{goal_id}/requirements")
def requirements(goal_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    owned_goal(db, user.id, goal_id)
    return [dump(row) for row in db.execute(select(GoalRequirement).where(GoalRequirement.goal_id == goal_id)).scalars().all()]


@router.post("/goals/{goal_id}/requirements", status_code=201)
def create_requirement(goal_id: str, payload: RequirementInput, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    owned_goal(db, user.id, goal_id)
    row = GoalRequirement(goal_id=goal_id, **payload.model_dump(mode="json")); db.add(row); db.commit(); db.refresh(row)
    return dump(row)


@router.patch("/goals/{goal_id}/requirements/{requirement_id}")
def update_requirement(goal_id: str, requirement_id: str, payload: RequirementUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    owned_goal(db, user.id, goal_id)
    row = db.execute(select(GoalRequirement).where(GoalRequirement.id == requirement_id, GoalRequirement.goal_id == goal_id)).scalar_one_or_none()
    if row is None: raise HTTPException(404, "要求不存在")
    for key, value in payload.model_dump(exclude_unset=True).items(): setattr(row, key, value)
    db.commit(); db.refresh(row); return dump(row)


@router.delete("/goals/{goal_id}/requirements/{requirement_id}", status_code=204)
def delete_requirement(goal_id: str, requirement_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    owned_goal(db, user.id, goal_id)
    row = db.execute(select(GoalRequirement).where(GoalRequirement.id == requirement_id, GoalRequirement.goal_id == goal_id)).scalar_one_or_none()
    if row is None: raise HTTPException(404, "要求不存在")
    db.delete(row); db.commit()


@router.get("/goals/{goal_id}/gaps")
def gaps(goal_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    try: return GoalGapAnalysisService().analyze(db, user.id, goal_id)
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc


def plan_response(db: Session, plan) -> dict:
    return {**dump(plan), "items": [dump(item) for item in db.execute(select(WeeklyPlanItem).where(WeeklyPlanItem.plan_id == plan.id)).scalars().all()]}


@router.post("/weekly-plans", status_code=201)
def generate_plan(goal_id: str | None = None, review_id: str | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    try: return plan_response(db, WeeklyTaskPlanningService().generate(db, user.id, goal_id, review_id))
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc


@router.post("/weekly-plans/{plan_id}/confirm")
def confirm_plan(plan_id: str, payload: PlanConfirmation, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    try: return plan_response(db, WeeklyTaskPlanningService().confirm(db, user.id, plan_id, payload.accepted_item_ids))
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc
