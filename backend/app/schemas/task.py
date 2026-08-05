from datetime import datetime

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    task_type: str = Field(pattern=r"^(main|support|challenge|subtask)$")
    parent_task_id: str | None = None
    status: str = Field(default="pending")
    deadline: datetime | None = None
    estimated_minutes: int | None = Field(default=None, ge=0)
    completion_standard: str | None = None
    evidence_requirements: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    status: str | None = None
    deadline: datetime | None = None
    estimated_minutes: int | None = Field(default=None, ge=0)
    completion_standard: str | None = None
    evidence_requirements: str | None = None


class TaskRead(TaskCreate):
    id: str
    parent_task_id: str | None = None

    model_config = {"from_attributes": True}
