from typing import Literal
from pydantic import BaseModel, Field
from app.schemas.growth import ATTRIBUTE_KEYS, CourseGradeInput, ExperienceInput, RequirementInput

class AISettingInput(BaseModel): allow_material_analysis: bool
class MaterialAIResult(BaseModel): courses:list[CourseGradeInput]=Field(default_factory=list); experiences:list[ExperienceInput]=Field(default_factory=list); missing_information:list[str]=Field(default_factory=list)
class GoalAIInput(BaseModel): supplied_text:str=Field(min_length=1,max_length=50000); source_type:Literal["user_input","supplied_document"]="user_input"
class GoalAIResult(BaseModel): requirements:list[RequirementInput]=Field(default_factory=list); time_nodes:list[str]=Field(default_factory=list); missing_information:list[str]=Field(default_factory=list); relationship_explanation:str
class DiagnosisAIResult(BaseModel): explanation:str; key_evidence_ids:list[str]=Field(default_factory=list); low_confidence_reasons:list[str]=Field(default_factory=list); needed_evidence:list[str]=Field(default_factory=list); priority_improvement:str
class PlanAIItem(BaseModel): id:str; title:str=Field(min_length=1,max_length=200); completion_standard:str=Field(min_length=1); evidence_requirements:str=Field(min_length=1); generation_reason:str=Field(min_length=1)
class PlanAIResult(BaseModel): items:list[PlanAIItem]
class FeedbackAIResult(BaseModel): summary:str; strengths:list[str]=Field(default_factory=list); incomplete_parts:list[str]=Field(default_factory=list); suggestions:list[str]=Field(default_factory=list); followup_questions:list[str]=Field(default_factory=list,max_length=5)
class FollowupAIResult(BaseModel): questions:list[str]=Field(min_length=1,max_length=5)
class FollowupAnswerInput(BaseModel): answer:str=Field(min_length=1,max_length=10000)
class FollowupEvaluationResult(BaseModel): evaluation:str
