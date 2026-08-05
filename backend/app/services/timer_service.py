from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.task import LearningSession, Task
from app.schemas.timer import TimerSessionRead, TimerStart


def elapsed_since(start_time: datetime | None, now: datetime) -> int:
    if start_time is None:
        return 0
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    return max(0, int((now - start_time).total_seconds()))


def start_timer(db: Session, user_id: str, payload: TimerStart) -> TimerSessionRead:
    if payload.task_id and db.execute(select(Task).where(Task.id == payload.task_id, Task.user_id == user_id)).scalar_one_or_none() is None:
        raise ValueError("任务不存在")
    session = LearningSession(user_id=user_id, task_id=payload.task_id, start_time=datetime.now(timezone.utc), is_running=True)
    db.add(session)
    db.commit()
    db.refresh(session)
    return TimerSessionRead.model_validate(session)


def pause_timer(db: Session, user_id: str, session_id: str) -> TimerSessionRead:
    session = db.execute(select(LearningSession).where(LearningSession.id == session_id, LearningSession.user_id == user_id)).scalar_one_or_none()
    if session is None:
        raise ValueError("计时记录不存在")
    if not session.is_running or session.end_time is not None:
        raise ValueError("计时器当前不能暂停")
    now = datetime.now(timezone.utc)
    elapsed = elapsed_since(session.start_time, now)
    session.elapsed_seconds += elapsed
    session.is_running = False
    db.commit()
    db.refresh(session)
    return TimerSessionRead.model_validate(session)


def continue_timer(db: Session, user_id: str, session_id: str) -> TimerSessionRead:
    session = db.execute(select(LearningSession).where(LearningSession.id == session_id, LearningSession.user_id == user_id)).scalar_one_or_none()
    if session is None:
        raise ValueError("计时记录不存在")
    if session.is_running or session.end_time is not None:
        raise ValueError("计时器当前不能恢复")
    session.start_time = datetime.now(timezone.utc)
    session.is_running = True
    db.commit()
    db.refresh(session)
    return TimerSessionRead.model_validate(session)


def end_timer(db: Session, user_id: str, session_id: str) -> TimerSessionRead:
    session = db.execute(select(LearningSession).where(LearningSession.id == session_id, LearningSession.user_id == user_id)).scalar_one_or_none()
    if session is None:
        raise ValueError("计时记录不存在")
    if session.end_time is not None:
        raise ValueError("计时器已经结束")
    now = datetime.now(timezone.utc)
    if session.start_time and session.is_running:
        session.elapsed_seconds += elapsed_since(session.start_time, now)
    session.is_running = False
    session.end_time = now
    db.commit()
    db.refresh(session)
    return TimerSessionRead.model_validate(session)


def list_sessions(db: Session, user_id: str) -> list[TimerSessionRead]:
    sessions = db.execute(select(LearningSession).where(LearningSession.user_id == user_id)).scalars().all()
    return [TimerSessionRead.model_validate(session) for session in sessions]
