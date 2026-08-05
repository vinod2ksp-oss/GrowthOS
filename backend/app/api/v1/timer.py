from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.timer import TimerSessionRead, TimerStart
from app.services.timer_service import continue_timer, end_timer, list_sessions, pause_timer, start_timer

router = APIRouter(tags=["timer"])


@router.get("/timers", response_model=list[TimerSessionRead])
def list_timer_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[TimerSessionRead]:
    return list_sessions(db, current_user.id)


@router.post("/timers/start", response_model=TimerSessionRead)
def start_timer_session(payload: TimerStart, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> TimerSessionRead:
    try:
        return start_timer(db, current_user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/timers/{session_id}/pause", response_model=TimerSessionRead)
def pause_timer_session(session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> TimerSessionRead:
    try:
        return pause_timer(db, current_user.id, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/timers/{session_id}/continue", response_model=TimerSessionRead)
def continue_timer_session(session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> TimerSessionRead:
    try:
        return continue_timer(db, current_user.id, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/timers/{session_id}/end", response_model=TimerSessionRead)
def end_timer_session(session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> TimerSessionRead:
    try:
        return end_timer(db, current_user.id, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
