from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.goal import GoalCreate, GoalRead, GoalUpdate
from app.services.goal_service import create_goal, list_goals, update_goal

router = APIRouter(tags=["goals"])


@router.get("/goals", response_model=list[GoalRead])
def list_goal_items(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[GoalRead]:
    return list_goals(db, current_user.id)


@router.post("/goals", response_model=GoalRead)
def create_goal_item(payload: GoalCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> GoalRead:
    return create_goal(db, current_user.id, payload)


@router.patch("/goals/{goal_id}", response_model=GoalRead)
def update_goal_item(goal_id: str, payload: GoalUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> GoalRead:
    try:
        return update_goal(db, current_user.id, goal_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
