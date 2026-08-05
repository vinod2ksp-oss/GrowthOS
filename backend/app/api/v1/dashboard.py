from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.goal_service import list_goals
from app.services.task_service import list_tasks

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    return {
        "goal_count": len(list_goals(db, current_user.id)),
        "task_count": len(list_tasks(db, current_user.id)),
        "status": "ready",
    }
