from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.models.task import Evidence, LearningSession, TaskEvaluation
from app.models.user import User
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services.evaluation_service import evaluate_task
from app.services.task_service import create_task, get_task, list_tasks, update_task

router = APIRouter(tags=["tasks"])


@router.get("/tasks", response_model=list[TaskRead])
def list_task_items(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[TaskRead]:
    return list_tasks(db, current_user.id)


@router.get("/tasks/{task_id}", response_model=TaskRead)
def get_task_item(task_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> TaskRead:
    task = get_task(db, current_user.id, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    return task


@router.post("/tasks", response_model=TaskRead)
def create_task_item(payload: TaskCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> TaskRead:
    try:
        return create_task(db, current_user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch("/tasks/{task_id}", response_model=TaskRead)
def update_task_item(task_id: str, payload: TaskUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> TaskRead:
    try:
        return update_task(db, current_user.id, task_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/tasks/{task_id}/evaluations", status_code=status.HTTP_201_CREATED)
def submit_task_evaluation(task_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    task = get_task(db, current_user.id, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    sessions = db.execute(select(LearningSession).where(LearningSession.user_id == current_user.id, LearningSession.task_id == task_id)).scalars().all()
    evidences = db.execute(select(Evidence).where(Evidence.user_id == current_user.id, Evidence.task_id == task_id)).scalars().all()
    result = evaluate_task(task, sessions, evidences)
    evaluation = TaskEvaluation(user_id=current_user.id, task_id=task_id, **result)
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    return {"id": evaluation.id, "task_id": task_id, **result}


@router.get("/tasks/{task_id}/evaluations/latest")
def latest_task_evaluation(task_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    if get_task(db, current_user.id, task_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    evaluation = db.execute(
        select(TaskEvaluation).where(TaskEvaluation.user_id == current_user.id, TaskEvaluation.task_id == task_id)
        .order_by(TaskEvaluation.created_at.desc())
    ).scalars().first()
    if evaluation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评测结果不存在")
    return {"id": evaluation.id, "task_id": task_id, "status": evaluation.status, "reason": evaluation.reason}
