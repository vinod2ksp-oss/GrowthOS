from pydantic import BaseModel, Field


class GoalCreate(BaseModel):
    target_school: str | None = None
    target_college: str | None = None
    target_major: str | None = None
    target_year: int | None = Field(default=None, ge=2024)
    weekly_time: int | None = Field(default=None, ge=0)
    current_stage: str | None = None
    remark: str | None = None


class GoalUpdate(BaseModel):
    target_school: str | None = None
    target_college: str | None = None
    target_major: str | None = None
    target_year: int | None = Field(default=None, ge=2024)
    weekly_time: int | None = Field(default=None, ge=0)
    current_stage: str | None = None
    remark: str | None = None


class GoalRead(GoalCreate):
    id: str

    model_config = {"from_attributes": True}
