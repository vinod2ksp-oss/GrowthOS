from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl

ATTRIBUTE_KEYS = Literal["mathematical_foundation", "english", "professional_knowledge", "academic_research", "data_analysis", "practical_experience", "programming_tools", "communication", "task_execution", "learning_stability"]


class CourseGradeInput(BaseModel):
    course_name: str = Field(min_length=1, max_length=200)
    course_category: ATTRIBUTE_KEYS
    score: float = Field(ge=0)
    full_score: float = Field(gt=0)
    credit: float | None = Field(default=None, ge=0)
    semester: str | None = Field(default=None, max_length=80)
    is_core: bool = False


class ExperienceInput(BaseModel):
    experience_type: Literal["research", "internship", "project", "competition", "certificate", "test_result", "portfolio", "other"]
    name: str = Field(min_length=1, max_length=255)
    organization: str | None = Field(default=None, max_length=255)
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = None
    outcome: str | None = None
    associated_skills: list[ATTRIBUTE_KEYS] = []


class MaterialConfirmation(BaseModel):
    courses: list[CourseGradeInput] = []
    experiences: list[ExperienceInput] = []


class RequirementInput(BaseModel):
    category: ATTRIBUTE_KEYS | Literal["other"]
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    metric_type: Literal["ratio", "score", "qualitative", "count"]
    target_min: float | None = None
    target_max: float | None = None
    unit: str | None = Field(default=None, max_length=40)
    importance: Literal["low", "medium", "high"] = "medium"
    source_type: Literal["official", "user_input", "supplied_document", "reference", "system_inference"]
    source_url: HttpUrl | None = None
    applicable_year: int | None = Field(default=None, ge=2000, le=2200)
    verification_status: Literal["pending", "confirmed", "outdated"] = "pending"


class RequirementUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    target_min: float | None = None
    target_max: float | None = None
    importance: Literal["low", "medium", "high"] | None = None
    verification_status: Literal["pending", "confirmed", "outdated"] | None = None


class PlanConfirmation(BaseModel):
    accepted_item_ids: list[str] | None = None


class TaskOutcomeInput(BaseModel):
    outcome_type: Literal["diagnostic_completed", "learning_verified", "mistake_archive", "project_result", "task_result"]
    attribute_key: ATTRIBUTE_KEYS | None = None


class InventoryPreferenceInput(BaseModel):
    user_note: str | None = Field(default=None, max_length=2000)
    hidden_from_current_goal: bool = False


class ReviewInput(BaseModel):
    period_start: date
    goal_id: str | None = None


class PlanItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    estimated_minutes: int | None = Field(default=None, ge=15)
    completion_standard: str | None = None
    evidence_requirements: str | None = None
    accepted: bool | None = None
