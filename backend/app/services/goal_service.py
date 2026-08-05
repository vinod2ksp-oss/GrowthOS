from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.goal import StudyGoal
from app.schemas.goal import GoalCreate, GoalRead, GoalUpdate


def create_goal(db: Session, user_id: str, payload: GoalCreate) -> GoalRead:
    goal = StudyGoal(user_id=user_id, **payload.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return GoalRead.model_validate(goal)


def list_goals(db: Session, user_id: str) -> list[GoalRead]:
    goals = db.execute(select(StudyGoal).where(StudyGoal.user_id == user_id)).scalars().all()
    return [GoalRead.model_validate(goal) for goal in goals]


def update_goal(db: Session, user_id: str, goal_id: str, payload: GoalUpdate) -> GoalRead:
    goal = db.execute(select(StudyGoal).where(StudyGoal.id == goal_id, StudyGoal.user_id == user_id)).scalar_one_or_none()
    if goal is None:
        raise ValueError("目标不存在")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(goal, field, value)
    goal.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(goal)
    return GoalRead.model_validate(goal)
