from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate


def create_task(db: Session, user_id: str, payload: TaskCreate) -> TaskRead:
    if payload.parent_task_id:
        parent = db.execute(select(Task).where(Task.id == payload.parent_task_id, Task.user_id == user_id)).scalar_one_or_none()
        if parent is None:
            raise ValueError("父任务不存在")
    task = Task(user_id=user_id, **payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return TaskRead.model_validate(task)


def list_tasks(db: Session, user_id: str) -> list[TaskRead]:
    tasks = db.execute(select(Task).where(Task.user_id == user_id)).scalars().all()
    return [TaskRead.model_validate(task) for task in tasks]


def get_task(db: Session, user_id: str, task_id: str) -> TaskRead | None:
    task = db.execute(select(Task).where(Task.id == task_id, Task.user_id == user_id)).scalar_one_or_none()
    if task is None:
        return None
    return TaskRead.model_validate(task)


def update_task(db: Session, user_id: str, task_id: str, payload: TaskUpdate) -> TaskRead:
    task = db.execute(select(Task).where(Task.id == task_id, Task.user_id == user_id)).scalar_one_or_none()
    if task is None:
        raise ValueError("任务不存在")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    task.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)
    return TaskRead.model_validate(task)
