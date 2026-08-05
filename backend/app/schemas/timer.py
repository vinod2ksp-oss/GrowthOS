from datetime import datetime

from pydantic import BaseModel


class TimerStart(BaseModel):
    task_id: str | None = None


class TimerSessionRead(BaseModel):
    id: str
    task_id: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    pause_total_seconds: int = 0
    elapsed_seconds: int = 0
    is_running: bool = False

    model_config = {"from_attributes": True}
