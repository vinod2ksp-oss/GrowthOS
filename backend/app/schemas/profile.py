from pydantic import BaseModel, Field


class ProfileCreate(BaseModel):
    nickname: str | None = None
    learning_stage: str | None = None
    grade_level: str | None = None
    school: str | None = None
    major: str | None = None
    auxiliary_direction: str | None = None
    weekly_study_hours: int | None = Field(default=None, ge=0)
    display_mode: str | None = None
    resource_budget: float | None = Field(default=None, ge=0)


class ProfileRead(ProfileCreate):
    id: str

    model_config = {"from_attributes": True}
